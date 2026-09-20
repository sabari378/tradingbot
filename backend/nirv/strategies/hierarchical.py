from dataclasses import dataclass

from nirv.market.candles import Candle, swing_highs, swing_lows

from .fair_value_gap import fair_value_gaps
from .liquidity_sweep import liquidity_sweep
from .market_structure import detect_mss


@dataclass(frozen=True)
class HierarchicalSetup:
    direction: str | None
    stop_loss: float | None
    reasons: list[str]


def _bias(candles: list[Candle]) -> str | None:
    if len(candles) < 21:
        return None
    average = sum(candle.close for candle in candles[-20:]) / 20
    slope = candles[-1].close - candles[-5].close
    if candles[-1].close > average and slope > 0:
        return "BUY"
    if candles[-1].close < average and slope < 0:
        return "SELL"
    return None


def _m15_confirmation(candles: list[Candle], direction: str) -> bool:
    if len(candles) < 22:
        return False
    history = candles[-21:-1]
    buy_level = max(candle.high for candle in history)
    sell_level = min(candle.low for candle in history)
    sweep = (
        liquidity_sweep(candles, "sell_side", sell_level)
        if direction == "BUY"
        else liquidity_sweep(candles, "buy_side", buy_level)
    )
    mss = detect_mss(candles, 2)
    expected_mss = "bullish" if direction == "BUY" else "bearish"
    return sweep and mss == expected_mss


def _m5_retracement(candles: list[Candle], direction: str) -> bool:
    if len(candles) < 25:
        return False
    gaps = fair_value_gaps(candles[:-1])
    expected = "bullish" if direction == "BUY" else "bearish"
    matching = [gap for gap in gaps if gap["direction"] == expected]
    if not matching:
        return False
    gap = matching[-1]
    current = candles[-1]
    overlaps = current.low <= float(gap["high"]) and current.high >= float(gap["low"])
    confirmation = current.bullish if direction == "BUY" else current.bearish
    return overlaps and confirmation


def _structure_stop(candles: list[Candle], direction: str, buffer_atr: float) -> float | None:
    if len(candles) < 20:
        return None
    entry = candles[-1].close
    average_range = sum(candle.high - candle.low for candle in candles[-15:]) / 15
    buffer = average_range * buffer_atr
    if direction == "BUY":
        levels = [candles[index].low for index in swing_lows(candles[:-1], 2) if candles[index].low < entry]
        return max(levels) - buffer if levels else None
    levels = [candles[index].high for index in swing_highs(candles[:-1], 2) if candles[index].high > entry]
    return min(levels) + buffer if levels else None


def analyze_hierarchical_setup(
    h1: list[Candle], m15: list[Candle], m5: list[Candle], *, stop_buffer_atr: float = 0.1
) -> HierarchicalSetup:
    direction = _bias(h1)
    if direction is None:
        return HierarchicalSetup(None, None, ["h1_bias_missing"])
    if not _m15_confirmation(m15, direction):
        return HierarchicalSetup(None, None, [f"h1_{direction.lower()}", "m15_confirmation_missing"])
    if not _m5_retracement(m5, direction):
        return HierarchicalSetup(None, None, [f"h1_{direction.lower()}", "m15_confirmed", "m5_retracement_missing"])
    stop_loss = _structure_stop(m5, direction, stop_buffer_atr)
    if stop_loss is None:
        return HierarchicalSetup(None, None, ["structure_stop_missing"])
    return HierarchicalSetup(direction, stop_loss, ["h1_bias", "m15_sweep_mss", "m5_fvg_confirmation"])


def analyze_balanced_setup(
    h1: list[Candle], m15: list[Candle], m5: list[Candle], *, stop_buffer_atr: float = 0.1
) -> HierarchicalSetup:
    direction = _bias(h1)
    if direction is None:
        return HierarchicalSetup(None, None, ["h1_bias_missing"])
    m15_mss = detect_mss(m15, 2)
    gaps = fair_value_gaps(m15)
    latest_gap = gaps[-1]["direction"] if gaps else None
    expected = "bullish" if direction == "BUY" else "bearish"
    if m15_mss != expected and latest_gap != expected:
        return HierarchicalSetup(None, None, [f"h1_{direction.lower()}", "m15_alignment_missing"])
    if len(m5) < 3:
        return HierarchicalSetup(None, None, ["m5_data_missing"])
    current, previous = m5[-1], m5[-2]
    momentum = (
        current.bullish and current.close > previous.high
        if direction == "BUY"
        else current.bearish and current.close < previous.low
    )
    if not momentum:
        return HierarchicalSetup(None, None, [f"h1_{direction.lower()}", "m15_aligned", "m5_momentum_missing"])
    stop_loss = _structure_stop(m5, direction, stop_buffer_atr)
    if stop_loss is None:
        return HierarchicalSetup(None, None, ["structure_stop_missing"])
    return HierarchicalSetup(direction, stop_loss, ["h1_bias", "m15_mss_or_fvg", "m5_momentum"])


def analyze_venus_setup(
    h1: list[Candle], m15: list[Candle], m5: list[Candle], *, stop_buffer_atr: float = 0.1
) -> HierarchicalSetup:
    del h1
    if len(m15) < 22 or len(m5) < 3:
        return HierarchicalSetup(None, None, ["market_data_missing"])
    current_m15 = m15[-1]
    history = m15[-21:-1]
    prior_high = max(candle.high for candle in history)
    prior_low = min(candle.low for candle in history)
    if current_m15.high > prior_high and current_m15.close < prior_high:
        direction = "SELL"
        sweep_extreme = current_m15.high
    elif current_m15.low < prior_low and current_m15.close > prior_low:
        direction = "BUY"
        sweep_extreme = current_m15.low
    else:
        return HierarchicalSetup(None, None, ["m15_liquidity_sweep_missing"])
    current_m5, previous_m5 = m5[-1], m5[-2]
    confirmed = (
        current_m5.bearish and current_m5.close < previous_m5.low
        if direction == "SELL"
        else current_m5.bullish and current_m5.close > previous_m5.high
    )
    if not confirmed:
        return HierarchicalSetup(None, None, [f"m15_{direction.lower()}_sweep", "m5_reversal_missing"])
    average_range = sum(candle.high - candle.low for candle in m15[-15:]) / 15
    buffer = average_range * stop_buffer_atr
    stop_loss = sweep_extreme + buffer if direction == "SELL" else sweep_extreme - buffer
    return HierarchicalSetup(direction, stop_loss, ["m15_liquidity_sweep", "m5_reversal_confirmation"])


def risk_sized_volume(
    *, equity: float, risk_percent: float, stop_distance: float, tick_size: float, tick_value: float,
    volume_min: float, volume_step: float, volume_max: float, safety_max: float
) -> float:
    if min(equity, risk_percent, stop_distance, tick_size, tick_value, volume_min, volume_step) <= 0:
        raise ValueError("risk-sizing inputs must be positive")
    risk_amount = equity * risk_percent / 100
    loss_per_lot = stop_distance / tick_size * tick_value
    raw = risk_amount / loss_per_lot
    if raw < volume_min:
        raise ValueError("broker minimum volume exceeds the configured risk limit")
    capped = min(raw, volume_max, safety_max)
    steps = int((capped - volume_min) / volume_step)
    return round(max(volume_min, volume_min + max(0, steps) * volume_step), 8)
