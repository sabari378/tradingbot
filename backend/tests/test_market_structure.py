from nirv.market.candles import Candle, swing_highs, swing_lows
from nirv.strategies.market_structure import detect_bos


def test_swing_high_and_low_detection() -> None:
    candles = [
        Candle(1, 2, 0.5, 1),
        Candle(1, 3, 0.8, 2),
        Candle(2, 2, 1, 1.5),
        Candle(1.5, 2.5, 0.7, 2),
        Candle(2, 2.2, 1.2, 1.8),
    ]
    assert 1 in swing_highs(candles, 1)
    assert 3 in swing_lows(candles, 1)


def test_bullish_and_bearish_bos() -> None:
    bullish = [Candle(1, 2, 0.5, 1), Candle(1, 1.5, 0.8, 1.2), Candle(1.2, 2.5, 1, 2.4)]
    bearish = [Candle(2, 2.5, 1.5, 2), Candle(2, 2.2, 1.8, 2), Candle(2, 2.1, 0.8, 1)]
    assert detect_bos(bullish, 1) == "bullish"
    assert detect_bos(bearish, 1) == "bearish"
