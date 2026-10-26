from typing import Any

import httpx


class TradingJourneyClient:
    def __init__(self, base_url: str, api_key: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    async def sync_trade(self, payload: dict[str, Any]) -> bool:
        return await self._post("/trades", payload)

    async def sync_analysis(self, payload: dict[str, Any]) -> bool:
        return await self._post("/analyses", payload)

    async def sync_trade_close(self, payload: dict[str, Any]) -> bool:
        return await self._post("/trades/close", payload)

    async def _post(self, path: str, payload: dict[str, Any]) -> bool:
        if not self.base_url:
            return False
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"{self.base_url}{path}", json=payload, headers=self.headers)
        return response.is_success
