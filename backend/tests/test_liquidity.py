from nirv.market.candles import Candle
from nirv.strategies.liquidity_sweep import equal_highs, equal_lows, liquidity_sweep


def test_equal_levels_and_sweeps() -> None:
    candles = [Candle(1, 10, 8, 9), Candle(9, 10.02, 8, 8.5)]
    assert equal_highs(candles)
    assert equal_lows(candles)
    assert liquidity_sweep([Candle(9, 11, 8, 9)], "buy_side", 10)
    assert liquidity_sweep([Candle(9, 10, 7, 9)], "sell_side", 8)
