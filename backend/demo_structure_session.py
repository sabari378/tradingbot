import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote as quote_path

import httpx

from nirv.execution.demo import DemoExecutionEngine
from nirv.market.candles import Candle
from nirv.schemas.trade import TradeCandidate
from nirv.strategies.setup import SetupDecision, analyze_setup


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a bounded multi-timeframe MT5 DEMO structure-stop session.")
    parser.add_argument("--symbol", default="GOLD.i#")
    parser.add_argument("--timeframes", default="M5,M15,H1")
    parser.add_argument("--duration", type=int, default=28800)
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--volume", type=float, default=0.05)
    parser.add_argument("--risk-reward", type=float, default=2.0)
    parser.add_argument("--stop-buffer-atr", type=float, default=0.1)
    parser.add_argument("--min-stop-distance", type=float, default=1.0)
    parser.add_argument("--max-stop-distance", type=float, default=25.0)
    parser.add_argument("--gateway", default="http://127.0.0.1:8100")
    parser.add_argument("--backend", default="http://127.0.0.1:8000")
    parser.add_argument("--output", default="backend/data/gold-demo-structure-8h.jsonl")
    return parser.parse_args()


def write_event(handle: Any, event: dict[str, Any]) -> None:
    handle.write(json.dumps(event, separators=(",", ":")) + "\n")
    handle.flush()


def candles_from_payload(payload: list[dict[str, Any]]) -> list[Candle]:
    return [
        Candle(
            float(item["open"]),
            float(item["high"]),
            float(item["low"]),
            float(item["close"]),
            float(item["volume"]),
        )
        for item in payload
    ]


def aligned_structure(setup: SetupDecision) -> bool:
    names = set(setup.confluence.confluences)
    return ({"bullish_mss", "bullish_fvg"} <= names) or ({"bearish_mss", "bearish_fvg"} <= names)


async def run_session(args: argparse.Namespace) -> None:
    engine = DemoExecutionEngine()
    account = await engine.account()
    if not account.get("connected") or account.get("mode") != "DEMO":
        raise RuntimeError(f"demo account validation failed: {account}")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    timeframes = [value.strip().upper() for value in args.timeframes.split(",") if value.strip()]
    processed_candles: set[tuple[str, int]] = set()
    priority = {"M5": 1, "M15": 2, "H1": 3}
    symbol_path = quote_path(args.symbol, safe="")

    with output.open("a", encoding="utf-8") as handle:
        started = datetime.now(timezone.utc)
        write_event(
            handle,
            {
                "event": "STRUCTURE_DEMO_STARTED",
                "started_at": started.isoformat(),
                "symbol": args.symbol,
                "timeframes": timeframes,
                "duration_seconds": args.duration,
                "volume": args.volume,
                "risk_reward": args.risk_reward,
                "stop_method": "support_resistance_zone",
                "trailing_enabled": False,
            },
        )
        end_at = asyncio.get_running_loop().time() + args.duration
        async with (
            httpx.AsyncClient(base_url=args.gateway, timeout=15) as market_client,
            httpx.AsyncClient(base_url=args.backend, timeout=5) as control_client,
        ):
            while asyncio.get_running_loop().time() < end_at:
                control = await control_client.get("/api/v1/controls/emergency-stop")
                control.raise_for_status()
                if control.json().get("active"):
                    write_event(handle, {"event": "STRUCTURE_DEMO_STOPPED", "reason": "emergency_stop"})
                    break

                positions = await engine.positions(args.symbol)
                quote_response = await market_client.get(f"/symbol/{symbol_path}")
                quote_response.raise_for_status()
                quote = quote_response.json()
                candidates: list[dict[str, Any]] = []

                for timeframe in timeframes:
                    response = await market_client.get(f"/candles/{symbol_path}/{timeframe}", params={"limit": 200})
                    response.raise_for_status()
                    payload = response.json()
                    if not payload:
                        continue
                    candle_time = int(payload[-1]["time"])
                    candle_key = (timeframe, candle_time)
                    if candle_key in processed_candles:
                        continue
                    processed_candles.add(candle_key)
                    setup = analyze_setup(
                        candles_from_payload(payload),
                        news_blocked=False,
                        risk_reward=args.risk_reward,
                        stop_method="structure",
                        stop_buffer_atr=args.stop_buffer_atr,
                    )
                    write_event(
                        handle,
                        {
                            "event": "STRUCTURE_SCAN",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "timeframe": timeframe,
                            "candle_time": candle_time,
                            "direction": setup.confluence.direction,
                            "score": setup.confluence.score,
                            "confluences": setup.confluence.confluences,
                            "stop_loss": setup.stop_loss,
                            "take_profit": setup.take_profit,
                            "broker_positions": len(positions),
                        },
                    )
                    if aligned_structure(setup) and setup.stop_loss is not None:
                        candidates.append({"timeframe": timeframe, "candle_time": candle_time, "setup": setup})

                if not positions and candidates:
                    selected = max(
                        candidates,
                        key=lambda item: (item["setup"].confluence.score, priority.get(item["timeframe"], 0)),
                    )
                    setup = selected["setup"]
                    direction = setup.confluence.direction
                    entry = float(quote["ask"] if direction == "BUY" else quote["bid"])
                    stop_loss = float(setup.stop_loss)
                    stop_distance = abs(entry - stop_loss)
                    valid_side = stop_loss < entry if direction == "BUY" else stop_loss > entry
                    valid_distance = args.min_stop_distance <= stop_distance <= args.max_stop_distance
                    if valid_side and valid_distance:
                        take_profit = (
                            entry + stop_distance * args.risk_reward
                            if direction == "BUY"
                            else entry - stop_distance * args.risk_reward
                        )
                        trade = TradeCandidate(
                            symbol=args.symbol,
                            direction=direction,
                            entry=entry,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            volume=args.volume,
                            risk_percent=0.25,
                            risk_reward=args.risk_reward,
                            confidence=min(1.0, setup.confluence.score / 4),
                            status="APPROVED",
                            mode="DEMO",
                        )
                        try:
                            filled = await engine.execute(trade)
                            write_event(
                                handle,
                                {
                                    "event": "STRUCTURE_DEMO_FILLED",
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                    "trade_id": str(filled.id),
                                    "broker_ticket": filled.broker_ticket,
                                    "timeframe": selected["timeframe"],
                                    "candle_time": selected["candle_time"],
                                    "direction": direction,
                                    "entry": entry,
                                    "stop_loss": stop_loss,
                                    "take_profit": take_profit,
                                    "stop_distance": stop_distance,
                                    "volume": args.volume,
                                },
                            )
                        except ValueError as error:
                            write_event(
                                handle,
                                {
                                    "event": "STRUCTURE_DEMO_REJECTED",
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                    "reason": str(error),
                                },
                            )
                    else:
                        write_event(
                            handle,
                            {
                                "event": "STRUCTURE_DEMO_REJECTED",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "reason": "invalid_zone_stop",
                                "direction": direction,
                                "entry": entry,
                                "stop_loss": stop_loss,
                                "stop_distance": stop_distance,
                            },
                        )

                await asyncio.sleep(min(args.interval, max(0, end_at - asyncio.get_running_loop().time())))

        remaining = await engine.positions(args.symbol)
        write_event(
            handle,
            {
                "event": "STRUCTURE_DEMO_FINISHED",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "open_positions": len(remaining),
            },
        )


if __name__ == "__main__":
    asyncio.run(run_session(parse_args()))
