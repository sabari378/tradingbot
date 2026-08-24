import pytest
from httpx import ASGITransport, AsyncClient

from nirv.api.main import app


@pytest.mark.asyncio
async def test_live_analysis_returns_a_market_response() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/analysis/live", params={"symbol": "BTCUSD#"})
    assert response.status_code in {200, 503}
    if response.status_code == 200:
        body = response.json()
        assert body["market_data_connected"] is True
        assert body["snapshot"]["candle_count"] > 0