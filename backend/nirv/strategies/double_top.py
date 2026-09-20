from dataclasses import dataclass
from statistics import median

from nirv.market.candles import Candle, swing_highs


@dataclass(frozen=True)
class DoubleTopSetup:
    direction: str | None
    first_peak: float | None
    second_peak: float | None
    neckline: float | None
    stop_loss: float | None
    reasons: list[str]


def analyze_double_top_displacement(
    candles: list[Candle],
    *,
    peak_tolerance_atr: float = 0.25,
    displacement_multiplier: float = 1.5,
    stop_buffer_atr: float = 0.1,
    minimum_peak_separation: int = 3,
    maximum_trigger_bars: int = 4,
) -> DoubleTopSetup:
    if len(candles) < 13:
        return DoubleTopSetup(None, None, None, None, None, ["market_data_missing"])

    trigger = candles[-1]
    context = candles[:-1]
    ranges = [candle.high - candle.low for candle in context[-20:]]
    average_range = sum(ranges) / len(ranges)
    bodies = [abs(candle.close - candle.open) for candle in context[-20:]]
    typical_body = median(bodies)
    peaks = swing_highs(context, 2)
    if len(peaks) < 2:
        return DoubleTopSetup(None, None, None, None, None, ["double_top_missing"])

    first_index, second_index = peaks[-2], peaks[-1]
    separation = second_index - first_index
    if separation < minimum_peak_separation:
        return DoubleTopSetup(None, None, None, None, None, ["peaks_too_close"])
    if len(candles) - 1 - second_index > maximum_trigger_bars:
        return DoubleTopSetup(None, None, None, None, None, ["second_peak_stale"])

    first_peak = context[first_index].high
    second_peak = context[second_index].high
    tolerance = average_range * peak_tolerance_atr
    if abs(first_peak - second_peak) > tolerance:
        return DoubleTopSetup(None, first_peak, second_peak, None, None, ["peak_tolerance_failed"])

    neckline = min(candle.low for candle in context[first_index + 1 : second_index])
    bearish_displacement = (
        trigger.bearish
        and abs(trigger.close - trigger.open) >= typical_body * displacement_multiplier
        and trigger.close < context[-1].low
    )
    if not bearish_displacement:
        return DoubleTopSetup(None, first_peak, second_peak, neckline, None, ["bearish_displacement_missing"])

    stop_loss = max(first_peak, second_peak) + average_range * stop_buffer_atr
    return DoubleTopSetup(
        "SELL",
        first_peak,
        second_peak,
        neckline,
        stop_loss,
        ["double_top", "bearish_displacement", "previous_low_break"],
    )
