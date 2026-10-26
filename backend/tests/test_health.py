import pytest
from httpx import ASGITransport, AsyncClient

from nirv.api.main import app


@pytest.mark.asyncio
async def test_health_is_paper_mode() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["mode"] == "PAPER"


@pytest.mark.asyncio
async def test_agents_endpoint_lists_nirv_agents() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/agents")
    names = {agent["name"] for agent in response.json()}
    assert {"master", "chart", "liquidity", "volume", "news", "signal", "risk", "execution"} <= names
