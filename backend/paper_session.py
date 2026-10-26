import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote as quote_path

import httpx

from nirv.market.candles import Candle
from nirv.strategies.setup import SetupDecision, analyze_setup


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a bounded MT5-backed paper trading session.")
    parser.add_argument("--symbol", default="BTCUSD#")
    parser.add_argument("--timeframe", default="M5")
    parser.add_argument("--duration", type=int, default=3600, help="Session length in seconds.")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between scans.")
    parser.add_argument("--gateway", default="http://127.0.0.1:8100")
    parser.add_argument("--output", default="backend/data/paper-session.jsonl")
    parser.add_argument("--strategy-id", default="baseline")
    parser.add_argument("--signals", default="liquidity,mss,fvg")
    parser.add_argument("--require-volume", action="store_true")
    parser.add_argument("--risk-reward", type=float, default=2.0)
    parser.add_argument(
        "--allow-no-news",
        action="store_true",
        help="Run the strategy experiment without a news provider; this never enables real execution.",
    )
    return parser.parse_args()


def write_event(handle: Any, event: dict[str, Any]) -> None:
    handle.write(json.dumps(event, separators=(",", ":")) + "\n")
    handle.flush()


def candles_from_payload(payload: list[dict[str, Any]]) -> list[Candle]:
    return [
        Candle(
            open=float(item["open"]),
            high=float(item["high"]),
            low=float(item["low"]),
            close=float(item["close"]),
            volume=float(item["volume"]),
        )
        for item in payload
    ]


def check_position(position: dict[str, Any], bid: float, ask: float) -> str | None:
    price = bid if position["direction"] == "SELL" else ask
    if position["direction"] == "SELL":
        if price >= position["stop_loss"]:
            return "STOP_LOSS"
        if price <= position["take_profit"]:
            return "TAKE_PROFIT"
    else:
        if price <= position["stop_loss"]:
            return "STOP_LOSS"
        if price >= position["take_profit"]:
            return "TAKE_PROFIT"
    return None


async def run_session(args: argparse.Namespace) -> None:
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc)
    position: dict[str, Any] | None = None
    last_quote: dict[str, Any] | None = None
    enabled_signals = {signal.strip().lower() for signal in args.signals.split(",") if signal.strip()}

    handle = output_path.open("a", encoding="utf-8")
    async with httpx.AsyncClient(base_url=args.gateway, timeout=15) as client:
        symbol_path = quote_path(args.symbol, safe="")
        write_event(
            handle,
            {
                "event": "SESSION_STARTED",
                "started_at": started.isoformat(),
                "symbol": args.symbol,
                "mode": "PAPER",
                "strategy_id": args.strategy_id,
                "signals": sorted(enabled_signals),
                "require_volume": args.require_volume,
                "risk_reward": args.risk_reward,
            },
        )
        end_at = asyncio.get_running_loop().time() + args.duration
        while asyncio.get_running_loop().time() < end_at:
            now = datetime.now(timezone.utc)
            candles_response = await client.get(f"/candles/{symbol_path}/{args.timeframe}", params={"limit": 200})
            candles_response.raise_for_status()
            quote_response = await client.get(f"/symbol/{symbol_path}")
            quote_response.raise_for_status()
            quote = quote_response.json()
            last_quote = quote
            candles = candles_from_payload(candles_response.json())
            setup: SetupDecision = analyze_setup(
                candles,
                news_blocked=not args.allow_no_news,
                risk_reward=args.risk_reward,
                use_liquidity="liquidity" in enabled_signals,
                use_mss="mss" in enabled_signals,
                use_fvg="fvg" in enabled_signals,
                use_volume=args.strategy_id == "baseline" or args.require_volume,
                require_volume=args.require_volume,
            )
            event: dict[str, Any] = {
                "event": "SCAN",
                "timestamp": now.isoformat(),
                "symbol": args.symbol,
                "bid": quote.get("bid"),
                "ask": quote.get("ask"),
                "candle_count": len(candles),
                "direction": setup.confluence.direction,
                "score": setup.confluence.score,
                "confluences": setup.confluence.confluences,
                "volume_confirmed": setup.volume_confirmed,
                "entry": setup.entry,
                "stop_loss": setup.stop_loss,
                "take_profit": setup.take_profit,
                "position_open": position is not None,
            }
            write_event(handle, event)

            if position is not None:
                exit_reason = check_position(position, float(quote["bid"]), float(quote["ask"]))
                if exit_reason:
                    exit_price = float(quote["bid"] if position["direction"] == "SELL" else quote["ask"])
                    pnl_points = (
                        position["entry"] - exit_price
                        if position["direction"] == "SELL"
                        else exit_price - position["entry"]
                    )
                    write_event(
                        handle,
                        {
                            "event": "PAPER_CLOSED",
                            "timestamp": now.isoformat(),
                            "reason": exit_reason,
                            "entry": position["entry"],
                            "exit": exit_price,
                            "pnl_points": round(pnl_points, 2),
                        },
                    )
                    position = None
            elif setup.confluence.direction and setup.entry is not None:
                entry = float(quote["bid"] if setup.confluence.direction == "SELL" else quote["ask"])
                position = {
                    "direction": setup.confluence.direction,
                    "entry": entry,
                    "stop_loss": setup.stop_loss,
                    "take_profit": setup.take_profit,
                }
                write_event(handle, {"event": "PAPER_OPENED", "timestamp": now.isoformat(), **position})

            await asyncio.sleep(min(args.interval, max(0, end_at - asyncio.get_running_loop().time())))

        if position is not None and last_quote is not None:
            exit_price = float(last_quote["bid"] if position["direction"] == "SELL" else last_quote["ask"])
            pnl_points = (
                position["entry"] - exit_price
                if position["direction"] == "SELL"
                else exit_price - position["entry"]
            )
            write_event(
                handle,
                {
                    "event": "PAPER_CLOSED",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "reason": "SESSION_END",
                    "entry": position["entry"],
                    "exit": exit_price,
                    "pnl_points": round(pnl_points, 2),
                },
            )
            position = None
        write_event(
            handle,
            {
                "event": "SESSION_FINISHED",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "position_open": position is not None,
            },
        )
    handle.close()


if __name__ == "__main__":
    asyncio.run(run_session(parse_args()))
