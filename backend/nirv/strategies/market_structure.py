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
