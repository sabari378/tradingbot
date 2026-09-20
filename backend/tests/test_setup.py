from nirv.market.candles import Candle
from nirv.strategies.confluence import evaluate_confluence
from nirv.strategies.hierarchical import analyze_balanced_setup, analyze_venus_setup, risk_sized_volume
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


def test_setup_does_not_reuse_an_old_fair_value_gap() -> None:
    candles = [Candle(100, 101, 99, 100, 10)] * 22
    candles.extend(
        [
            Candle(100, 101, 99, 100, 10),
            Candle(102, 103, 102, 102.5, 10),
            Candle(104, 105, 103, 104, 10),
            Candle(104, 105, 103, 104, 10),
        ]
    )

    decision = analyze_setup(
        candles,
        news_blocked=False,
        use_liquidity=False,
        use_mss=False,
        use_fvg=True,
        use_volume=False,
    )

    assert decision.confluence.direction is None


def test_confluence_accepts_one_directional_strategy() -> None:
    decision = evaluate_confluence(
        sweep=None, mss="bullish", fvg=None, volume_confirmed=False, news_blocked=False
    )

    assert decision.direction == "BUY"
    assert decision.confluences == ["bullish_mss"]
    assert decision.score == 1


def test_confluence_rejects_conflicting_strategies() -> None:
    decision = evaluate_confluence(
        sweep=None, mss="bullish", fvg="bearish", volume_confirmed=True, news_blocked=False
    )

    assert decision.direction is None
    assert decision.score == 0


def test_risk_sizing_reduces_volume_for_wider_stop() -> None:
    narrow = risk_sized_volume(
        equity=10_000,
        risk_percent=0.25,
        stop_distance=5,
        tick_size=0.01,
        tick_value=1,
        volume_min=0.01,
        volume_step=0.01,
        volume_max=1,
        safety_max=0.05,
    )
    wide = risk_sized_volume(
        equity=10_000,
        risk_percent=0.25,
        stop_distance=20,
        tick_size=0.01,
        tick_value=1,
        volume_min=0.01,
        volume_step=0.01,
        volume_max=1,
        safety_max=0.05,
    )
    assert narrow >= wide
    assert narrow <= 0.05


def test_balanced_setup_requires_h1_bias() -> None:
    candles = [Candle(100, 101, 99, 100, 10)] * 25
    decision = analyze_balanced_setup(candles, candles, candles)
    assert decision.direction is None
    assert decision.reasons == ["h1_bias_missing"]


def test_venus_setup_requires_liquidity_sweep() -> None:
    candles = [Candle(100, 101, 99, 100, 10)] * 25
    decision = analyze_venus_setup(candles, candles, candles)
    assert decision.direction is None
    assert decision.reasons == ["m15_liquidity_sweep_missing"]


def test_structure_stop_covers_latest_swing_and_new_sweep(monkeypatch) -> None:
    from nirv.strategies import setup
    from nirv.strategies.confluence import ConfluenceDecision

    candles = [Candle(105, 110, 100, 105)] * 22
    candles += [
        Candle(105, 110, 95, 105),
        Candle(105, 110, 101, 105),
        Candle(105, 110, 102, 105),
        Candle(105, 112, 90, 111),
    ]
    for direction, series in (
        ('BUY', candles),
        ('SELL', [Candle(220-c.open, 220-c.low, 220-c.high, 220-c.close) for c in candles]),
    ):
        monkeypatch.setattr(setup, 'evaluate_confluence', lambda **kwargs: ConfluenceDecision(direction, [], 1))
        result = setup.analyze_setup(series, stop_method='structure', stop_buffer_atr=0.1)
        if direction == 'BUY':
            assert result.stop_loss < 90
            assert result.take_profit > result.entry
        else:
            assert result.stop_loss > 130
            assert result.take_profit < result.entry


def test_structure_buffer_includes_gap_from_previous_close(monkeypatch) -> None:
    import pytest
    from nirv.strategies import setup
    from nirv.strategies.confluence import ConfluenceDecision

    candles = [Candle(100, 101, 99, 100)] * 25
    candles.append(Candle(110, 112, 109, 111))
    monkeypatch.setattr(setup, 'evaluate_confluence', lambda **kwargs: ConfluenceDecision('BUY', [], 1))
    result = setup.analyze_setup(candles, stop_method='structure', stop_buffer_atr=0.1)
    # Fourteen ranges of 2 and a final true range of 12, including the gap.
    assert result.stop_loss == pytest.approx(99 - (14 * 2 + 12) / 15 * 0.1)
