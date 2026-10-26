import pytest
from nirv.market.candles import Candle
from nirv.strategies.market_structure import detect_bos, fresh_bos_context
from nirv.strategies.catalog import CATALOG_STRATEGIES, evaluate_catalog_strategy


def series(previous, current):
    candles = [Candle(5, 9, 1, 5)] * 25
    candles += [Candle(5, 10, 0, 5), Candle(5, 8, 2, 5), Candle(5, 8, 2, 5)]
    candles += [Candle(5, max(9, previous), min(1, previous), previous)]
    return candles + [Candle(5, max(12, current), min(-2, current), current)]


@pytest.mark.parametrize("previous,current,direction", [(9,11,"bullish"),(10,11,"bullish"),(11,12,None),(1,-1,"bearish"),(0,-1,"bearish"),(-1,-2,None),(9,10,None),(1,0,None)])
def test_fresh_cross_uses_same_confirmed_level(previous, current, direction):
    result = fresh_bos_context(series(previous, current))
    assert result["swing_high"] == 10
    assert result["swing_low"] == 0
    assert result["direction"] == direction


def test_baseline_kept_and_repeat_filtered():
    candles = series(11, 12)
    assert detect_bos(candles) == "bullish"
    assert evaluate_catalog_strategy("market_structure", candles, risk_reward=2).confluence.direction == "BUY"
    assert evaluate_catalog_strategy("market_structure", candles, risk_reward=2, fresh_structure=True).confluence.direction is None


@pytest.mark.parametrize("name", [n for n in CATALOG_STRATEGIES if n != "market_structure"])
def test_other_strategies_unchanged(name):
    candles = series(9, 11)
    assert evaluate_catalog_strategy(name, candles, risk_reward=2) == evaluate_catalog_strategy(name, candles, risk_reward=2, fresh_structure=True)


def test_short_history():
    assert fresh_bos_context([])["direction"] is None
