from nirv.market.candles import Candle
from nirv.strategies.double_top import analyze_double_top_displacement


def test_detects_double_top_with_large_bearish_displacement() -> None:
    candles = [
        Candle(100, 102, 99, 101, 100),
        Candle(101, 103, 100, 102, 100),
        Candle(102, 105, 101, 104, 100),
        Candle(104, 110, 103, 106, 110),
        Candle(106, 107, 103, 104, 100),
        Candle(104, 106, 101, 103, 90),
        Candle(103, 105, 102, 104, 90),
        Candle(104, 108, 103, 107, 100),
        Candle(107, 110.2, 105, 108, 110),
        Candle(108, 109, 105, 106, 100),
        Candle(106, 107, 104, 105, 100),
        Candle(105, 106, 103, 104, 100),
        Candle(108, 109, 99, 100, 180),
    ]

    setup = analyze_double_top_displacement(candles)

    assert setup.direction == "SELL"
    assert setup.first_peak == 110
    assert setup.second_peak == 110.2
    assert setup.stop_loss > 110.2


def test_rejects_normal_sized_trigger_candle() -> None:
    candles = [Candle(100, 102, 99, 101, 100)] * 13
    assert analyze_double_top_displacement(candles).direction is None
