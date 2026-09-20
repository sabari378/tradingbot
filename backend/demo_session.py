import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from nirv.execution.demo import DemoExecutionEngine
from nirv.market.candles import Candle
from nirv.schemas.trade import TradeCandidate
from nirv.strategies.setup import analyze_setup


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a bounded MT5 demo-account trading session.")
    parser.add_argument("--symbol", default="GOLD.i#")
    parser.add_argument("--timeframe", default="M5")
    parser.add_argument("--duration", type=int, default=7200)
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--volume", type=float, default=0.05)
    parser.add_argument("--gateway", default="http://127.0.0.1:8100")
    parser.add_argument("--backend", default="http://127.0.0.1:8000")
    parser.add_argument("--output", default="backend/data/gold-demo-m5.jsonl")
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
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    engine = DemoExecutionEngine()
    account = await engine.account()
    if not account.get("connected") or account.get("mode") != "DEMO":
        raise RuntimeError(f"demo account validation failed: {account}")

    position_open = False
    handle = output_path.open("a", encoding="utf-8")
    try:
        started = datetime.now(timezone.utc)
        write_event(
            handle,
            {
                "event": "DEMO_SESSION_STARTED",
                "started_at": started.isoformat(),
                "symbol": args.symbol,
                "mode": "DEMO",
                "volume": args.volume,
            },
        )
        end_at = asyncio.get_running_loop().time() + args.duration
        async with (
            httpx.AsyncClient(base_url=args.gateway, timeout=15) as client,
            httpx.AsyncClient(base_url=args.backend, timeout=5) as control_client,
        ):
            while asyncio.get_running_loop().time() < end_at:
                control_response = await control_client.get("/api/v1/controls/emergency-stop")
                control_response.raise_for_status()
                if control_response.json().get("active"):
                    write_event(
                        handle,
                        {
                            "event": "DEMO_SESSION_STOPPED",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "reason": "emergency_stop",
                        },
                    )
                    break

                symbol_path = args.symbol.replace("#", "%23")
                candles_response = await client.get(f"/candles/{symbol_path}/{args.timeframe}", params={"limit": 200})
                quote_response = await client.get(f"/symbol/{symbol_path}")
                candles_response.raise_for_status()
                quote_response.raise_for_status()
                candles = candles_from_payload(candles_response.json())
                quote = quote_response.json()
                setup = analyze_setup(candles, news_blocked=False)
                price_action_vote = (
                    "BUY"
                    if setup.confluence.direction == "BUY" and "bullish_mss" in setup.confluence.confluences
                    else "SELL"
                    if setup.confluence.direction == "SELL" and "bearish_mss" in setup.confluence.confluences
                    else None
                )
                imbalance_vote = (
                    "BUY"
                    if setup.confluence.direction == "BUY" and "bullish_fvg" in setup.confluence.confluences
                    else "SELL"
                    if setup.confluence.direction == "SELL" and "bearish_fvg" in setup.confluence.confluences
                    else None
                )
                aligned = price_action_vote is not None and price_action_vote == imbalance_vote
                write_event(
                    handle,
                    {
                        "event": "DEMO_SCAN",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "symbol": args.symbol,
                        "price_action_vote": price_action_vote,
                        "imbalance_vote": imbalance_vote,
                        "aligned": aligned,
                        "position_open": position_open,
                        "bid": quote.get("bid"),
                        "ask": quote.get("ask"),
                    },
                )

                setup_ready = setup.entry is not None and setup.stop_loss is not None and setup.take_profit is not None
                if not position_open and aligned and setup_ready:
                    direction = price_action_vote
                    trade = TradeCandidate(
                        symbol=args.symbol,
                        direction=direction,
                        entry=float(quote["ask"] if direction == "BUY" else quote["bid"]),
                        stop_loss=setup.stop_loss,
                        take_profit=setup.take_profit,
                        volume=args.volume,
                        risk_percent=0.25,
                        risk_reward=2.0,
                        confidence=setup.confluence.score / 4,
                        status="APPROVED",
                        mode="DEMO",
                    )
                    filled = await engine.execute(trade)
                    position_open = True
                    write_event(
                        handle,
                        {
                            "event": "DEMO_ORDER_FILLED",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "trade_id": str(filled.id),
                            "direction": direction,
                            "volume": args.volume,
                            "broker_ticket": filled.broker_ticket,
                        },
                    )

                await asyncio.sleep(min(args.interval, max(0, end_at - asyncio.get_running_loop().time())))
        write_event(
            handle,
            {
                "event": "DEMO_SESSION_FINISHED",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "position_open": position_open,
            },
        )
    finally:
        handle.close()


if __name__ == "__main__":
    asyncio.run(run_session(parse_args()))