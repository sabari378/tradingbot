from datetime import datetime, timezone

import httpx

from nirv.core.config import get_settings
from nirv.core.enums import TradeStatus
from nirv.schemas.trade import TradeCandidate


class DemoExecutionEngine:
    @staticmethod
    def _headers() -> dict[str, str]:
        return {"X-Nirv-Signature": get_settings().mt5_gateway_secret}

    async def account(self) -> dict:
        settings = get_settings()
        headers = self._headers()
        async with httpx.AsyncClient(base_url=settings.mt5_gateway_url, timeout=10) as client:
            response = await client.get("/account", headers=headers)
        if response.status_code != 200:
            raise ValueError(f"MT5 gateway returned HTTP {response.status_code}")
        return response.json()

    async def positions(self, symbol: str | None = None) -> list[dict]:
        settings = get_settings()
        async with httpx.AsyncClient(base_url=settings.mt5_gateway_url, timeout=10) as client:
            response = await client.get(
                "/positions", params={"symbol": symbol} if symbol else None, headers=self._headers()
            )
        if response.status_code != 200:
            raise ValueError(f"MT5 gateway returned HTTP {response.status_code}")
        return response.json()

    async def close_position(self, *, ticket: str, symbol: str, volume: float, magic: int) -> dict:
        settings = get_settings()
        payload = {"ticket": ticket, "symbol": symbol, "volume": volume, "magic": magic, "mode": "DEMO"}
        async with httpx.AsyncClient(base_url=settings.mt5_gateway_url, timeout=10) as client:
            response = await client.post("/orders/close", json=payload, headers=self._headers())
        response.raise_for_status()
        result = response.json()
        if not result.get("success"):
            raise ValueError(result.get("error", "MT5 close failed"))
        return result

    async def modify_position(
        self, *, ticket: str, symbol: str, stop_loss: float, take_profit: float
    ) -> dict:
        settings = get_settings()
        payload = {
            "ticket": ticket,
            "symbol": symbol,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "mode": "DEMO",
        }
        async with httpx.AsyncClient(base_url=settings.mt5_gateway_url, timeout=10) as client:
            response = await client.post("/positions/modify", json=payload, headers=self._headers())
        response.raise_for_status()
        result = response.json()
        if not result.get("success"):
            raise ValueError(result.get("error", "MT5 modification failed"))
        return result

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
            "magic": getattr(trade, "magic", 1302015909),
        }
        headers = self._headers()
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
