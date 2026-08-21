from nirv.market.candles import Candle


def fair_value_gaps(candles: list[Candle]) -> list[dict[str, float | str]]:
    gaps: list[dict[str, float | str]] = []
    for index in range(2, len(candles)):
        left, right = candles[index - 2], candles[index]
        if left.high < right.low:
            gaps.append({"direction": "bullish", "low": left.high, "high": right.low})
        elif left.low > right.high:
            gaps.append({"direction": "bearish", "low": right.high, "high": left.low})
    return gaps
