from typing import Any

from nirv.market.candles import Candle, swing_highs, swing_lows
from nirv.strategies.double_top import analyze_double_top_displacement
from nirv.strategies.market_structure import detect_bos


def analyze_price_action(raw_candles: list[dict[str, Any]], lookback: int = 2) -> dict[str, list[dict]]:
    candles = [
        Candle(
            open=float(item["open"]),
            high=float(item["high"]),
            low=float(item["low"]),
            close=float(item["close"]),
            volume=float(item.get("volume", 0)),
        )
        for item in raw_candles
    ]
    swings: list[dict] = []
    previous_high = previous_low = None
    high_indexes = set(swing_highs(candles, lookback))
    low_indexes = set(swing_lows(candles, lookback))
    for index, candle in enumerate(candles):
        if index in high_indexes:
            label = "HH" if previous_high is None or candle.high > previous_high else "LH"
            swings.append({"time": raw_candles[index]["time"], "price": candle.high, "kind": label})
            previous_high = candle.high
        if index in low_indexes:
            label = "LL" if previous_low is None or candle.low < previous_low else "HL"
            swings.append({"time": raw_candles[index]["time"], "price": candle.low, "kind": label})
            previous_low = candle.low

    breaks: list[dict] = []
    patterns: list[dict] = []
    pattern_peaks: set[tuple[int, int]] = set()
    active_break: str | None = None
    for index in range(max(5, lookback + 2), len(candles)):
        window_start = max(0, index + 1 - 200)
        window = candles[window_start : index + 1]
        direction = detect_bos(window, lookback)
        if direction and direction != active_break:
            breaks.append(
                {
                    "time": raw_candles[index]["time"],
                    "price": candles[index].close,
                    "direction": direction,
                    "label": "BOS UP" if direction == "bullish" else "BOS DOWN",
                }
            )
        active_break = direction

        double_top = analyze_double_top_displacement(window)
        if double_top.direction:
            peaks = swing_highs(window[:-1], 2)
            if len(peaks) >= 2:
                first = window_start + peaks[-2]
                second = window_start + peaks[-1]
                key = (first, second)
                if key not in pattern_peaks:
                    pattern_peaks.add(key)
                    patterns.append(
                        {
                            "type": "double_top",
                            "label": "DOUBLE TOP",
                            "first_time": raw_candles[first]["time"],
                            "second_time": raw_candles[second]["time"],
                            "trigger_time": raw_candles[index]["time"],
                            "first_peak": double_top.first_peak,
                            "second_peak": double_top.second_peak,
                            "neckline": double_top.neckline,
                        }
                    )

    return {"swings": swings, "breaks": breaks, "patterns": patterns}
