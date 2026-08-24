from datetime import datetime, timezone

import httpx

from nirv.core.config import get_settings
from nirv.core.enums import TradeStatus
from nirv.schemas.trade import TradeCandidate


class DemoExecutionEngine:
    async def account(self) -> dict:
        settings = get_settings()
        headers = {"X-Nirv-Signature": settings.mt5_gateway_secret}
        async with httpx.AsyncClient(base_url=settings.mt5_gateway_url, timeout=10) as client:
            response = await client.get("/account", headers=headers)
        if response.status_code != 200:
            raise ValueError(f"MT5 gateway returned HTTP {response.status_code}")
        return response.json()

    async def execute(self, trade: TradeCandidate) -> TradeCandidate:
        if trade.status != TradeStatus.APPROVED:
            raise ValueError("trade must be approved before execution")

        settings = get_settings()
        payload = {
            "trade_id": str(trade.id),
            "symbol": trade.symbol,
            "side": trade.direction.value,
            "volume": trade.volume,
            "stop_loss": trade.stop_loss,
            "take_profit": trade.take_profit,
            "mode": "DEMO",
        }
        headers = {"X-Nirv-Signature": settings.mt5_gateway_secret}
        async with httpx.AsyncClient(base_url=settings.mt5_gateway_url, timeout=10) as client:
            response = await client.post("/orders", json=payload, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"MT5 gateway returned HTTP {response.status_code}")
        result = response.json()
        if not result.get("success"):
            raise ValueError(result.get("error", "MT5 order failed"))
        return trade.model_copy(
            update={
                "status": TradeStatus.FILLED,
                "executed_at": datetime.now(timezone.utc),
                "broker_ticket": result.get("ticket"),
            }
        )