import pytest

from nirv.market.candles import Candle
from nirv.strategies.catalog import evaluate_catalog_strategy


def test_sma_crossover_detects_a_fresh_bullish_cross() -> None:
    candles = [Candle(100, 101, 99, 100, 100) for _ in range(50)]
    candles.append(Candle(100, 201, 99, 200, 200))

    decision = evaluate_catalog_strategy("sma_crossover", candles, risk_reward=2)

    assert decision.confluence.direction == "BUY"
    assert decision.stop_loss < decision.entry < decision.take_profit


def test_sma_crossover_waits_for_full_slow_average() -> None:
    candles = [Candle(100, 101, 99, 100, 100) for _ in range(25)]
    decision = evaluate_catalog_strategy("sma_crossover", candles, risk_reward=2)
    assert decision.confluence.direction is None


def test_donchian_breakout_uses_the_prior_range() -> None:
    candles = [Candle(100, 101, 99, 100, 100) for _ in range(24)]
    candles.append(Candle(100, 104, 99, 103, 200))

    decision = evaluate_catalog_strategy("donchian_breakout", candles, risk_reward=2)

    assert decision.confluence.direction == "BUY"


def test_bollinger_reversion_detects_a_new_lower_extreme() -> None:
    candles = [Candle(100, 102, 98, 99 if index % 2 else 101, 100) for index in range(24)]
    candles.append(Candle(99, 100, 89, 90, 200))

    decision = evaluate_catalog_strategy("bollinger_reversion", candles, risk_reward=2)

    assert decision.confluence.direction == "BUY"


def test_engulfing_reversal_requires_body_engulfment() -> None:
    candles = [Candle(100, 101, 99, 100, 100) for _ in range(23)]
    candles.extend([Candle(101, 102, 98, 99, 100), Candle(98, 103, 97, 102, 200)])

    decision = evaluate_catalog_strategy("engulfing_reversal", candles, risk_reward=2)

    assert decision.confluence.direction == "BUY"


def test_catalog_rejects_an_unknown_strategy() -> None:
    candles = [Candle(100, 101, 99, 100, 100) for _ in range(25)]
    with pytest.raises(ValueError, match="unknown catalog strategy"):
        evaluate_catalog_strategy("unknown", candles, risk_reward=2)
