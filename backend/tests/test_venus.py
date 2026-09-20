import pytest

from nirv.market.candles import Candle
from nirv.strategies.venus import reached_one_r, target_before_opposing_structure


def test_sell_target_stops_before_nearest_support() -> None:
    candles = [
        Candle(110, 112, 108, 111),
        Candle(111, 113, 107, 109),
        Candle(109, 110, 105, 109),
        Candle(109, 111, 107, 110),
        Candle(110, 111, 109, 110),
        Candle(110, 110, 109, 109),
        Candle(109, 110, 108, 109),
    ]
    target, risk_reward = target_before_opposing_structure(
        candles, "SELL", entry=110, stop_loss=115, desired_risk_reward=2, buffer_atr=0.1
    )

    assert 105 < target < 110
    assert risk_reward < 1


@pytest.mark.parametrize(
    ("direction", "entry", "stop", "current", "expected"),
    [("BUY", 100, 95, 105, True), ("BUY", 100, 95, 104.9, False), ("SELL", 100, 105, 95, True)],
)
def test_reached_one_r(direction, entry, stop, current, expected) -> None:
    assert reached_one_r(direction, entry, stop, current) is expected
