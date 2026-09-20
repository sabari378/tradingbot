from nirv.market.candles import Candle, swing_highs, swing_lows


def detect_bos(candles: list[Candle], lookback: int = 2) -> str | None:
    if len(candles) < lookback + 2:
        return None
    confirmed = candles[:-1]
    highs, lows = swing_highs(confirmed, lookback), swing_lows(confirmed, lookback)
    if not highs:
        prior_high = max(candle.high for candle in confirmed)
    else:
        prior_high = confirmed[highs[-1]].high
    if not lows:
        prior_low = min(candle.low for candle in confirmed)
    else:
        prior_low = confirmed[lows[-1]].low
    last = candles[-1]
    if last.close > prior_high:
        return "bullish"
    if last.close < prior_low:
        return "bearish"
    return None


def detect_mss(candles: list[Candle], lookback: int = 2) -> str | None:
    return detect_bos(candles, lookback)


def fresh_bos_context(candles: list[Candle], lookback: int = 2) -> dict:
    """Compare both closes with the same level, confirmed before the signal bar."""
    if len(candles) < lookback + 2:
        return {"direction": None, "reason": "insufficient_history"}
    confirmed = candles[:-1]
    highs, lows = swing_highs(confirmed, lookback), swing_lows(confirmed, lookback)
    high = confirmed[highs[-1]].high if highs else max(c.high for c in confirmed)
    low = confirmed[lows[-1]].low if lows else min(c.low for c in confirmed)
    previous, current = candles[-2].close, candles[-1].close
    direction = "bullish" if previous <= high < current else "bearish" if current < low <= previous else None
    return {"direction": direction, "swing_high": high, "swing_low": low,
            "previous_close": previous, "current_close": current,
            "reason": "fresh_break" if direction else "no_fresh_break"}
