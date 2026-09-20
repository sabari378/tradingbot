from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient, MockTransport, Request, Response

from nirv.agents.backtest import BacktestAgent
from nirv.api.main import app
from nirv.core.config import get_settings
from nirv.market.candles import Candle
from nirv.schemas.backtest import BacktestRequest
from nirv.strategies.confluence import ConfluenceDecision
from nirv.strategies.setup import SetupDecision


def backtest_request() -> BacktestRequest:
    return BacktestRequest(
        symbol="GOLD.i#",
        timeframe="M15",
        date_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
        date_to=datetime(2026, 1, 2, tzinfo=timezone.utc),
        signals=["fvg"],
        risk_reward=2,
    )


def test_next_candle_entry_charges_spread_and_uses_requested_risk_reward(monkeypatch) -> None:
    calls = 0

    def setup(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return SetupDecision(ConfluenceDecision("BUY", ["bullish_fvg"], 1), 100, 99, 102, False)
        return SetupDecision(ConfluenceDecision(None, [], 0), None, None, None, False)

    monkeypatch.setattr("nirv.agents.backtest.analyze_setup", setup)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    candles = [
        {
            "time": int((start + timedelta(minutes=15 * index)).timestamp()),
            "open": 100,
            "high": 103 if index == 26 else 100.5,
            "low": 99.5,
            "close": 100,
            "volume": 100,
            "spread": 2,
        }
        for index in range(27)
    ]

    result = BacktestAgent().run(backtest_request(), candles, point=0.1)

    assert result.metrics.trades == 1
    trade = result.trades[0]
    assert trade.signal_time == start + timedelta(minutes=15 * 24)
    assert trade.entry_time == start + timedelta(minutes=15 * 25)
    assert trade.entry == 100.2
    assert trade.take_profit == pytest.approx(102.6)
    assert trade.exit_reason == "TAKE_PROFIT"
    assert trade.pnl_r == 2


def test_same_candle_ambiguity_uses_stop_first() -> None:
    position = {
        "direction": "BUY",
        "signal_time": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "entry_time": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "entry": 100,
        "stop_loss": 99,
        "take_profit": 102,
        "risk": 1,
        "confluences": ["bullish_fvg"],
    }
    trade = BacktestAgent._close_position(
        position, Candle(100, 103, 98, 101), datetime(2026, 1, 1, 0, 15, tzinfo=timezone.utc), 0.1
    )
    assert trade is not None
    assert trade.exit_reason == "STOP_LOSS"
    assert trade.pnl_r == -1


@pytest.mark.asyncio
async def test_backtest_route_requires_api_key(monkeypatch) -> None:
    monkeypatch.setenv("API_KEY", "test-key")
    get_settings.cache_clear()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/backtests/run", json=backtest_request().model_dump(mode="json"))
        assert response.status_code == 401
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_backtest_route_uses_xm_history(monkeypatch) -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def gateway(request: Request) -> Response:
        if request.url.path.startswith("/historical-candles/"):
            candles = [
                {
                    "time": int((start + timedelta(minutes=15 * index)).timestamp()),
                    "open": 100,
                    "high": 101,
                    "low": 99,
                    "close": 100,
                    "volume": 100,
                    "spread": 2,
                }
                for index in range(25)
            ]
            return Response(200, json=candles)
        return Response(200, json={"available": True, "trade_tick_size": 0.1, "digits": 1})

    monkeypatch.setenv("API_KEY", "test-key")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "nirv.api.routes.backtests.httpx.AsyncClient",
        lambda **kwargs: AsyncClient(transport=MockTransport(gateway), base_url="http://gateway"),
    )
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/backtests/run",
                json=backtest_request().model_dump(mode="json"),
                headers={"X-API-Key": "test-key"},
            )
        assert response.status_code == 200
        assert response.json()["agent"] == "backtest"
        assert response.json()["metrics"]["candles"] == 25
    finally:
        get_settings.cache_clear()
