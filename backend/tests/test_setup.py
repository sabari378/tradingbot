from nirv.market.candles import Candle
from nirv.strategies.setup import analyze_setup


def test_setup_requires_enough_candles() -> None:
    decision = analyze_setup([Candle(100, 101, 99, 100, 10)] * 5)
    assert decision.confluence.direction is None
    assert decision.entry is None


def test_setup_blocks_news_blackout() -> None:
    candles = [Candle(100, 101, 99, 100, 10)] * 25
    decision = analyze_setup(candles, news_blocked=True)
    assert decision.confluence.direction is None
    assert "news_blackout" in decision.confluence.confluences