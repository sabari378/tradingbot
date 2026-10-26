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
from nirv.strategies.hierarchical import risk_sized_volume
from nirv.strategies.setup import SetupDecision, analyze_setup
from nirv.strategies.venus import reached_one_r, target_before_opposing_structure

MAGIC = 1302015913


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a bounded Venus v2 MT5 DEMO session.")
    parser.add_argument("--symbol", default="GOLD.i#")
    parser.add_argument("--timeframes", default="M5,M15,H1")
    parser.add_argument("--max-positions", type=int, default=1, help="0 allows unlimited concurrent positions")
    parser.add_argument("--reversal-timeframe", default="M5")
    parser.add_argument("--duration", type=int, default=18000)
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--risk-percent", type=float, default=0.25)
    parser.add_argument("--desired-risk-reward", type=float, default=2.0)
    parser.add_argument("--minimum-risk-reward", type=float, default=1.2)
    parser.add_argument("--max-volume", type=float, default=0.05)
    parser.add_argument("--stop-buffer-atr", type=float, default=0.1)
    parser.add_argument("--min-stop-distance", type=float, default=1.0)
    parser.add_argument("--max-stop-distance", type=float, default=25.0)
    parser.add_argument("--gateway", default="http://127.0.0.1:8100")
    parser.add_argument("--backend", default="http://127.0.0.1:8000")
    parser.add_argument("--output", default="backend/data/venus-v2-demo.jsonl")
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
    priority = {"M5": 1, "M15": 2, "M30": 3, "H1": 4}
    processed_candles: set[tuple[str, int]] = set()
    symbol_path = quote_path(args.symbol, safe="")
    managed_positions: dict[str, dict[str, Any]] = {}

    with output.open("a", encoding="utf-8") as handle:
        write_event(handle, {
            "event": "VENUS_V2_STARTED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": args.duration,
            "risk_percent": args.risk_percent,
            "timeframes": timeframes,
            "max_positions": args.max_positions,
            "management": ["structure_target", "one_r_partial", "breakeven", f"{args.reversal_timeframe.lower()}_reversal_exit"],
            "magic": MAGIC,
        })
        end_at = asyncio.get_running_loop().time() + args.duration
        async with (
            httpx.AsyncClient(base_url=args.gateway, timeout=15) as market,
            httpx.AsyncClient(base_url=args.backend, timeout=5) as control,
        ):
            while asyncio.get_running_loop().time() < end_at:
                response = await control.get("/api/v1/controls/emergency-stop")
                response.raise_for_status()
                if response.json().get("active"):
                    write_event(handle, {"event": "VENUS_V2_STOPPED", "reason": "emergency_stop"})
                    break

                all_positions = await engine.positions(args.symbol)
                own_positions = [position for position in all_positions if int(position.get("magic", 0)) == MAGIC]
                active_tickets = {str(p["ticket"]) for p in own_positions}
                for ticket in list(managed_positions):
                    if ticket not in active_tickets:
                        write_event(handle, {"event": "VENUS_V2_POSITION_CLOSED", "ticket": ticket})
                        del managed_positions[ticket]
                for position in own_positions:
                    ticket = str(position["ticket"])
                    if ticket in managed_positions:
                        continue
                    entry = float(position["price_open"])
                    current_stop = float(position["stop_loss"])
                    managed_positions[ticket] = {
                        "ticket": position["ticket"],
                        "direction": position["side"],
                        "entry": entry,
                        "initial_stop": current_stop,
                        "take_profit": float(position["take_profit"]),
                        "protected": abs(current_stop - entry) <= 0.05,
                    }
                    write_event(
                        handle,
                        {
                            "event": "VENUS_V2_RESUMED_POSITION",
                            "ticket": position["ticket"],
                            "direction": position["side"],
                            "entry": entry,
                            "stop_loss": current_stop,
                            "take_profit": float(position["take_profit"]),
                        },
                    )

                quote_response = await market.get(f"/symbol/{symbol_path}")
                quote_response.raise_for_status()
                details = quote_response.json()
                payloads: dict[str, list[dict[str, Any]]] = {}
                setups: dict[str, SetupDecision] = {}
                candidates: list[dict[str, Any]] = []
                for timeframe in timeframes:
                    candle_response = await market.get(f"/candles/{symbol_path}/{timeframe}", params={"limit": 200})
                    candle_response.raise_for_status()
                    payload = candle_response.json()
                    if not payload:
                        continue
                    payloads[timeframe] = payload
                    candle_time = int(payload[-1]["time"])
                    setup = analyze_setup(
                        candles_from_payload(payload),
                        news_blocked=False,
                        risk_reward=args.desired_risk_reward,
                        stop_method="structure",
                        stop_buffer_atr=args.stop_buffer_atr,
                    )
                    setups[timeframe] = setup
                    key = (timeframe, candle_time)
                    if key not in processed_candles:
                        processed_candles.add(key)
                        write_event(handle, {
                            "event": "VENUS_V2_SCAN",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "timeframe": timeframe,
                            "candle_time": candle_time,
                            "direction": setup.confluence.direction,
                            "score": setup.confluence.score,
                            "confluences": setup.confluence.confluences,
                            "positions": len(all_positions),
                        })
                        if aligned_structure(setup) and setup.stop_loss is not None:
                            candidates.append({"timeframe": timeframe, "candle_time": candle_time, "setup": setup})

                for position in own_positions:
                    ticket = str(position["ticket"])
                    managed = managed_positions[ticket]
                    current = float(position["price_current"])
                    m5_setup = setups.get(args.reversal_timeframe)
                    opposite = (
                        m5_setup is not None
                        and aligned_structure(m5_setup)
                        and m5_setup.confluence.direction != managed["direction"]
                    )
                    if opposite:
                        await engine.close_position(
                            ticket=position["ticket"], symbol=args.symbol, volume=float(position["volume"]), magic=MAGIC
                        )
                        write_event(
                            handle,
                            {"event": "VENUS_V2_REVERSAL_EXIT", "ticket": position["ticket"], "price": current},
                        )
                        managed_positions.pop(ticket, None)
                    elif not managed["protected"] and reached_one_r(
                        managed["direction"], managed["entry"], managed["initial_stop"], current
                    ):
                        volume = float(position["volume"])
                        step = float(details["volume_step"])
                        minimum = float(details["volume_min"])
                        partial = int((volume / 2) / step) * step
                        if minimum <= partial < volume:
                            await engine.close_position(
                                ticket=position["ticket"], symbol=args.symbol, volume=partial, magic=MAGIC
                            )
                        await engine.modify_position(
                            ticket=position["ticket"], symbol=args.symbol,
                            stop_loss=managed["entry"], take_profit=managed["take_profit"],
                        )
                        managed["protected"] = True
                        write_event(handle, {
                            "event": "VENUS_V2_ONE_R_PROTECTED", "ticket": position["ticket"],
                            "partial": partial if minimum <= partial < volume else 0, "breakeven": managed["entry"],
                        })

                for selected in sorted(candidates, key=lambda item: (item["setup"].confluence.score, priority.get(item["timeframe"], 0)), reverse=True):
                    if args.max_positions and len(managed_positions) >= args.max_positions:
                        break
                    setup = selected["setup"]
                    direction = setup.confluence.direction
                    entry = float(details["ask"] if direction == "BUY" else details["bid"])
                    stop_loss = float(setup.stop_loss)
                    distance = abs(entry - stop_loss)
                    valid_side = stop_loss < entry if direction == "BUY" else stop_loss > entry
                    if valid_side and args.min_stop_distance <= distance <= args.max_stop_distance:
                        target, actual_rr = target_before_opposing_structure(
                            candles_from_payload(payloads[selected["timeframe"]]), direction, entry, stop_loss,
                            desired_risk_reward=args.desired_risk_reward, buffer_atr=args.stop_buffer_atr,
                        )
                        if actual_rr >= args.minimum_risk_reward:
                            account = await engine.account()
                            try:
                                volume = risk_sized_volume(
                                    equity=float(account["equity"]), risk_percent=args.risk_percent,
                                    stop_distance=distance, tick_size=float(details["trade_tick_size"]),
                                    tick_value=float(details["trade_tick_value"]), volume_min=float(details["volume_min"]),
                                    volume_step=float(details["volume_step"]), volume_max=float(details["volume_max"]),
                                    safety_max=args.max_volume,
                                )
                            except ValueError as error:
                                write_event(handle, {"event": "VENUS_V2_REJECTED", "timestamp": datetime.now(timezone.utc).isoformat(), "reason": str(error)})
                                await asyncio.sleep(args.interval)
                                continue
                            trade = TradeCandidate(
                                symbol=args.symbol, direction=direction, entry=entry, stop_loss=stop_loss,
                                take_profit=target, volume=volume, risk_percent=args.risk_percent,
                                risk_reward=actual_rr, confidence=min(1.0, setup.confluence.score / 4),
                                status="APPROVED", mode="DEMO", magic=MAGIC,
                            )
                            try:
                                filled = await engine.execute(trade)
                            except (ValueError, httpx.HTTPError) as error:
                                write_event(handle, {"event": "VENUS_V2_ORDER_ERROR", "timestamp": datetime.now(timezone.utc).isoformat(), "reason": str(error)})
                                continue
                            managed_positions[str(filled.broker_ticket)] = {
                                "ticket": filled.broker_ticket, "direction": direction, "entry": entry,
                                "initial_stop": stop_loss, "take_profit": target, "protected": False,
                            }
                            write_event(handle, {
                                "event": "VENUS_V2_FILLED", "timestamp": datetime.now(timezone.utc).isoformat(),
                                "ticket": filled.broker_ticket, "timeframe": selected["timeframe"],
                                "direction": direction, "entry": entry, "stop_loss": stop_loss,
                                "take_profit": target, "risk_reward": actual_rr, "volume": volume,
                            })
                        else:
                            write_event(
                                handle,
                                {
                                    "event": "VENUS_V2_REJECTED",
                                    "reason": "opposing_structure_too_close",
                                    "risk_reward": actual_rr,
                                },
                            )

                await asyncio.sleep(min(args.interval, max(0, end_at - asyncio.get_running_loop().time())))

        write_event(handle, {"event": "VENUS_V2_FINISHED", "timestamp": datetime.now(timezone.utc).isoformat()})


if __name__ == "__main__":
    asyncio.run(run_session(parse_args()))
