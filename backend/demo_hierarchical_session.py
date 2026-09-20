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
from nirv.strategies.hierarchical import (
    analyze_balanced_setup,
    analyze_hierarchical_setup,
    analyze_venus_setup,
    risk_sized_volume,
)

MAGIC = 1302015910


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the risk-sized H1/M15/M5 MT5 DEMO strategy.")
    parser.add_argument("--symbol", default="GOLD.i#")
    parser.add_argument("--duration", type=int, default=28800)
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--risk-percent", type=float, default=0.25)
    parser.add_argument("--risk-reward", type=float, default=2.0)
    parser.add_argument("--max-volume", type=float, default=0.05)
    parser.add_argument("--min-stop-distance", type=float, default=1.0)
    parser.add_argument("--max-stop-distance", type=float, default=25.0)
    parser.add_argument("--gateway", default="http://127.0.0.1:8100")
    parser.add_argument("--backend", default="http://127.0.0.1:8000")
    parser.add_argument("--output", default="backend/data/gold-demo-hierarchical.jsonl")
    parser.add_argument("--strategy-mode", choices=("strict", "mercury", "venus"), default="strict")
    return parser.parse_args()


def write_event(handle: Any, event: dict[str, Any]) -> None:
    handle.write(json.dumps(event, separators=(",", ":")) + "\n")
    handle.flush()


def candles(payload: list[dict[str, Any]]) -> list[Candle]:
    return [Candle(item["open"], item["high"], item["low"], item["close"], item["volume"]) for item in payload]


async def run_session(args: argparse.Namespace) -> None:
    engine = DemoExecutionEngine()
    account = await engine.account()
    if not account.get("connected") or account.get("mode") != "DEMO":
        raise RuntimeError(f"demo account validation failed: {account}")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    symbol_path = quote_path(args.symbol, safe="")
    last_m5_candle: int | None = None
    managed: dict[str, Any] | None = None
    strategy_magic = 1302015911 if args.strategy_mode == "venus" else MAGIC

    with output.open("a", encoding="utf-8") as handle:
        write_event(
            handle,
            {
                "event": "HIERARCHICAL_STARTED",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "strategy_mode": args.strategy_mode,
            },
        )
        end_at = asyncio.get_running_loop().time() + args.duration
        async with (
            httpx.AsyncClient(base_url=args.gateway, timeout=15) as market,
            httpx.AsyncClient(base_url=args.backend, timeout=5) as control,
        ):
            while asyncio.get_running_loop().time() < end_at:
                stop = await control.get("/api/v1/controls/emergency-stop")
                stop.raise_for_status()
                if stop.json().get("active"):
                    write_event(handle, {"event": "HIERARCHICAL_STOPPED", "reason": "emergency_stop"})
                    break

                all_positions = await engine.positions(args.symbol)
                own_positions = [position for position in all_positions if position.get("magic") == strategy_magic]
                if managed and not own_positions:
                    write_event(handle, {"event": "HIERARCHICAL_POSITION_CLOSED", "ticket": managed["ticket"]})
                    managed = None

                if managed and own_positions and not managed["protected"]:
                    position = own_positions[0]
                    current = float(position["price_current"])
                    reached_one_r = (
                        current >= managed["one_r"]
                        if managed["side"] == "BUY"
                        else current <= managed["one_r"]
                    )
                    if reached_one_r:
                        info = await market.get(f"/symbol/{symbol_path}")
                        info.raise_for_status()
                        details = info.json()
                        remaining_volume = float(position["volume"])
                        partial = round(remaining_volume / 2 / details["volume_step"]) * details["volume_step"]
                        if details["volume_min"] <= partial < remaining_volume:
                            await engine.close_position(
                                ticket=position["ticket"], symbol=args.symbol, volume=partial, magic=strategy_magic
                            )
                        await engine.modify_position(
                            ticket=position["ticket"],
                            symbol=args.symbol,
                            stop_loss=managed["entry"],
                            take_profit=managed["take_profit"],
                        )
                        managed["protected"] = True
                        write_event(
                            handle,
                            {"event": "HIERARCHICAL_ONE_R_PROTECTED", "ticket": position["ticket"], "partial": partial},
                        )

                if not all_positions:
                    payloads: dict[str, list[dict[str, Any]]] = {}
                    for timeframe in ("M5", "M15", "H1"):
                        response = await market.get(f"/candles/{symbol_path}/{timeframe}", params={"limit": 200})
                        response.raise_for_status()
                        payloads[timeframe] = response.json()
                    candle_time = int(payloads["M5"][-1]["time"])
                    if candle_time != last_m5_candle:
                        last_m5_candle = candle_time
                        analyzers = {
                            "strict": analyze_hierarchical_setup,
                            "mercury": analyze_balanced_setup,
                            "venus": analyze_venus_setup,
                        }
                        analyzer = analyzers[args.strategy_mode]
                        setup = analyzer(candles(payloads["H1"]), candles(payloads["M15"]), candles(payloads["M5"]))
                        write_event(
                            handle,
                            {
                                "event": "HIERARCHICAL_SCAN",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "candle_time": candle_time,
                                "direction": setup.direction,
                                "reasons": setup.reasons,
                                "stop_loss": setup.stop_loss,
                            },
                        )
                        if setup.direction and setup.stop_loss:
                            quote_response = await market.get(f"/symbol/{symbol_path}")
                            quote_response.raise_for_status()
                            details = quote_response.json()
                            entry = float(details["ask"] if setup.direction == "BUY" else details["bid"])
                            distance = abs(entry - setup.stop_loss)
                            valid_side = (
                                setup.stop_loss < entry if setup.direction == "BUY" else setup.stop_loss > entry
                            )
                            if valid_side and args.min_stop_distance <= distance <= args.max_stop_distance:
                                account = await engine.account()
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
                                take_profit = (
                                    entry + distance * args.risk_reward
                                    if setup.direction == "BUY"
                                    else entry - distance * args.risk_reward
                                )
                                trade = TradeCandidate(
                                    symbol=args.symbol,
                                    direction=setup.direction,
                                    entry=entry,
                                    stop_loss=setup.stop_loss,
                                    take_profit=take_profit,
                                    volume=volume,
                                    risk_percent=args.risk_percent,
                                    risk_reward=args.risk_reward,
                                    confidence=1.0,
                                    status="APPROVED",
                                    mode="DEMO",
                                    magic=strategy_magic,
                                )
                                filled = await engine.execute(trade)
                                managed = {
                                    "ticket": filled.broker_ticket,
                                    "side": setup.direction,
                                    "entry": entry,
                                    "one_r": entry + distance if setup.direction == "BUY" else entry - distance,
                                    "take_profit": take_profit,
                                    "protected": False,
                                }
                                write_event(
                                    handle,
                                    {
                                        "event": "HIERARCHICAL_FILLED",
                                        "ticket": filled.broker_ticket,
                                        "direction": setup.direction,
                                        "entry": entry,
                                        "stop_loss": setup.stop_loss,
                                        "take_profit": take_profit,
                                        "volume": volume,
                                    },
                                )

                await asyncio.sleep(min(args.interval, max(0, end_at - asyncio.get_running_loop().time())))

        write_event(
            handle,
            {"event": "HIERARCHICAL_FINISHED", "timestamp": datetime.now(timezone.utc).isoformat()},
        )


if __name__ == "__main__":
    asyncio.run(run_session(parse_args()))
