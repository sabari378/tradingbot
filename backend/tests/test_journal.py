import pytest
from httpx import ASGITransport, AsyncClient

from nirv.api.main import app


@pytest.mark.asyncio
async def test_paper_history_endpoint_returns_records() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/paper-history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)