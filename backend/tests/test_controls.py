import pytest
from httpx import ASGITransport, AsyncClient

from nirv.api.main import app


@pytest.mark.asyncio
async def test_emergency_stop_blocks_execution() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/controls/emergency-stop")
    assert response.status_code == 200