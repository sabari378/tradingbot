from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from nirv.api.main import app
from nirv.core.config import get_settings


@pytest.mark.asyncio
async def test_protected_route_fails_closed_without_configured_key(monkeypatch) -> None:
    monkeypatch.setenv("API_KEY", "")
    get_settings.cache_clear()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/trades", json={})
        assert response.status_code == 503
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_help_voice_command_does_not_start_paper_session(monkeypatch) -> None:
    def unexpected_start() -> dict:
        raise AssertionError("paper session was started")

    monkeypatch.setattr("nirv.api.routes.voice.start_gold_paper_session", unexpected_start)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/voice/command", json={"text": "help"})
    assert response.status_code == 200
    assert response.json()["intent"] == "HELP"


@pytest.mark.asyncio
async def test_each_bot_can_describe_its_capability() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/voice/command",
            json={"text": "What can you do?", "target": "risk"},
        )
    assert response.status_code == 200
    assert response.json()["target"] == "risk"
    assert "Sentinel" in response.json()["response"]


@pytest.mark.asyncio
async def test_trade_create_rejects_server_owned_status(monkeypatch) -> None:
    monkeypatch.setenv("API_KEY", "test-key")
    get_settings.cache_clear()
    payload = {
        "id": str(uuid4()),
        "direction": "BUY",
        "entry": 100,
        "stop_loss": 99,
        "take_profit": 102,
        "risk_percent": 0.25,
        "confidence": 0.8,
        "status": "APPROVED",
    }
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/trades", json=payload, headers={"X-API-Key": "test-key"})
        assert response.status_code == 422
    finally:
        get_settings.cache_clear()
