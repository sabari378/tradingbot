from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class Quote:
    symbol: str
    bid: float
    ask: float
    timestamp: datetime
    is_mock: bool = False


class MarketDataProvider(Protocol):
    async def candles(self, symbol: str, timeframe: str, limit: int = 200) -> list[dict]: ...
    async def quote(self, symbol: str) -> Quote: ...
    async def spread(self, symbol: str) -> float: ...


class MockMarketDataProvider:
    async def candles(self, symbol: str, timeframe: str, limit: int = 200) -> list[dict]:
        return []

    async def quote(self, symbol: str) -> Quote:
        from datetime import timezone

        return Quote(symbol, 0, 0, datetime.now(timezone.utc), is_mock=True)

    async def spread(self, symbol: str) -> float:
        return 0
