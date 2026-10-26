import pytest

from nirv.core.config import Settings
from nirv.core.enums import TradeDirection
from nirv.risk.calculator import SymbolSpecification, calculate_position_size
from nirv.risk.policy import evaluate_risk


def settings() -> Settings:
    return Settings(
        max_risk_percent=0.5,
        max_daily_loss_percent=2,
        min_risk_reward=1.5,
        max_open_trades=1,
        max_spread=0.5,
        max_signal_age_seconds=300,
    )


def test_risk_rejects_invalid_trade_conditions() -> None:
    decision = evaluate_risk(
        direction=TradeDirection.BUY,
        entry=100,
        stop_loss=100,
        take_profit=101,
        risk_percent=1,
        daily_loss_percent=2,
        open_trades=1,
        spread=1,
        data_age_seconds=301,
        news_blocked=True,
        settings=settings(),
    )
    assert not decision.approved
    assert {
        "invalid_stop",
        "risk_too_high",
        "daily_loss_limit_exceeded",
        "maximum_open_trades_exceeded",
        "spread_too_high",
        "stale_market_data",
        "news_blackout",
    } <= set(decision.reasons)


def test_risk_accepts_valid_trade() -> None:
    decision = evaluate_risk(
        direction=TradeDirection.BUY,
        entry=100,
        stop_loss=99,
        take_profit=102,
        risk_percent=0.25,
        daily_loss_percent=0,
        open_trades=0,
        spread=0.1,
        data_age_seconds=10,
        news_blocked=False,
        settings=settings(),
    )
    assert decision.approved


def test_position_size_rejects_broker_minimum_that_exceeds_risk() -> None:
    specification = SymbolSpecification(symbol="XAUUSD", contract_size=100, min_volume=0.01)
    with pytest.raises(ValueError, match="broker minimum"):
        calculate_position_size(100, 0.01, 100, 90, specification)
