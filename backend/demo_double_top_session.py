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
from nirv.strategies.double_top import analyze_double_top_displacement
from nirv.strategies.hierarchical import risk_sized_volume

MAGIC = 1302015914


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the fast Double-Top Displacement DEMO strategy.")
    parser.add_argument("--symbol", default="GOLD.i#")
    parser.add_argument("--timeframe", default="M15")
    parser.add_argument("--duration", type=int, default=18000)
    parser.add_argument("--interval", type=int, default=5)
    parser.add_argument("--risk-percent", type=float, default=0.25)
    parser.add_argument("--risk-reward", type=float, default=0.8)
    parser.add_argument("--max-volume", type=float, default=0.05)
    parser.add_argument("--max-positions", type=int, default=2)
    parser.add_argument("--min-stop-distance", type=float, default=1.0)
    parser.add_argument("--max-stop-distance", type=float, default=25.0)
    parser.add_argument("--gateway", default="http://127.0.0.1:8100")
    parser.add_argument("--backend", default="http://127.0.0.1:8000")
    parser.add_argument("--output", default="backend/data/double-top-displacement-demo.jsonl")
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


async def run_session(args: argparse.Namespace) -> None:
    engine = DemoExecutionEngine()
    account = await engine.account()
    if not account.get("connected") or account.get("mode") != "DEMO":
        raise RuntimeError(f"demo account validation failed: {account}")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    symbol_path = quote_path(args.symbol, safe="")
    processed_signals: set[int] = set()
    last_heartbeat = 0.0

    with output.open("a", encoding="utf-8") as handle:
        write_event(handle, {
            "event": "DOUBLE_TOP_STARTED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": args.symbol,
            "timeframe": args.timeframe,
            "duration_seconds": args.duration,
            "interval_seconds": args.interval,
            "risk_percent": args.risk_percent,
            "risk_reward": args.risk_reward,
            "max_positions": args.max_positions,
            "forming_candle_enabled": True,
            "magic": MAGIC,
        })
        loop = asyncio.get_running_loop()
        end_at = loop.time() + args.duration
        async with (
            httpx.AsyncClient(base_url=args.gateway, timeout=10) as market,
            httpx.AsyncClient(base_url=args.backend, timeout=5) as control,
        ):
            while loop.time() < end_at:
                stop = await control.get("/api/v1/controls/emergency-stop")
                stop.raise_for_status()
                if stop.json().get("active"):
                    write_event(handle, {"event": "DOUBLE_TOP_STOPPED", "reason": "emergency_stop"})
                    break

                positions = await engine.positions(args.symbol)
                own_positions = [position for position in positions if int(position.get("magic", 0)) == MAGIC]
                candle_response = await market.get(
                    f"/candles/{symbol_path}/{args.timeframe}",
                    params={"limit": 200, "include_current": "true"},
                )
                candle_response.raise_for_status()
                payload = candle_response.json()
                if not payload:
                    await asyncio.sleep(args.interval)
                    continue
                current_bar_time = int(payload[-1]["time"])
                setup = analyze_double_top_displacement(candles_from_payload(payload))

                if loop.time() - last_heartbeat >= 60:
                    last_heartbeat = loop.time()
                    write_event(handle, {
                        "event": "DOUBLE_TOP_HEARTBEAT",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "current_bar_time": current_bar_time,
                        "direction": setup.direction,
                        "reasons": setup.reasons,
                        "strategy_positions": len(own_positions),
                        "all_positions": len(positions),
                    })

                if (
                    setup.direction == "SELL"
                    and setup.stop_loss is not None
                    and current_bar_time not in processed_signals
                    and (args.max_positions == 0 or len(own_positions) < args.max_positions)
                ):
                    quote_response = await market.get(f"/symbol/{symbol_path}")
                    quote_response.raise_for_status()
                    details = quote_response.json()
                    entry = float(details["bid"])
                    stop_loss = float(setup.stop_loss)
                    distance = stop_loss - entry
                    processed_signals.add(current_bar_time)
                    if args.min_stop_distance <= distance <= args.max_stop_distance:
                        account = await engine.account()
                        try:
                            volume = risk_sized_volume(
                                equity=float(account["equity"]),
                                risk_percent=args.risk_percent,
                                stop_distance=distance,
                                tick_size=float(details["trade_tick_size"]),
                                tick_value=float(details["trade_tick_value"]),
                                volume_min=float(details["volume_min"]),
                                volume_step=float(details["volume_step"]),
                                volume_max=float(details["volume_max"]),
                                safety_max=args.max_volume,
                            )
                        except ValueError as error:
                            write_event(handle, {"event": "DOUBLE_TOP_REJECTED", "timestamp": datetime.now(timezone.utc).isoformat(), "reason": str(error)})
                            await asyncio.sleep(args.interval)
                            continue
                        take_profit = entry - distance * args.risk_reward
                        trade = TradeCandidate(
                            symbol=args.symbol,
                            direction="SELL",
                            entry=entry,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            volume=volume,
                            risk_percent=args.risk_percent,
                            risk_reward=args.risk_reward,
                            confidence=0.75,
                            status="APPROVED",
                            mode="DEMO",
                            magic=MAGIC,
                        )
                        try:
                            filled = await engine.execute(trade)
                        except (ValueError, httpx.HTTPError) as error:
                            write_event(handle, {"event": "DOUBLE_TOP_ORDER_ERROR", "timestamp": datetime.now(timezone.utc).isoformat(), "reason": str(error)})
                            await asyncio.sleep(args.interval)
                            continue
                        write_event(handle, {
                            "event": "DOUBLE_TOP_FILLED",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "ticket": filled.broker_ticket,
                            "bar_time": current_bar_time,
                            "entry": entry,
                            "stop_loss": stop_loss,
                            "take_profit": take_profit,
                            "volume": volume,
                            "reasons": setup.reasons,
                        })
                    else:
                        write_event(handle, {
                            "event": "DOUBLE_TOP_REJECTED",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "reason": "invalid_stop_distance",
                            "stop_distance": distance,
                        })

                await asyncio.sleep(min(args.interval, max(0, end_at - loop.time())))

        write_event(handle, {"event": "DOUBLE_TOP_FINISHED", "timestamp": datetime.now(timezone.utc).isoformat()})


if __name__ == "__main__":
    asyncio.run(run_session(parse_args()))
