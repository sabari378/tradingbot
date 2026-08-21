from dataclasses import dataclass


@dataclass(frozen=True)
class Candle:
    open: float
    high: float
    low: float
    close: float
    volume: float = 0

    @property
    def bullish(self) -> bool:
        return self.close > self.open

    @property
    def bearish(self) -> bool:
        return self.close < self.open


def swing_highs(candles: list[Candle], lookback: int = 2) -> list[int]:
    return [
        index
        for index in range(lookback, len(candles) - lookback)
        if candles[index].high == max(candle.high for candle in candles[index - lookback : index + lookback + 1])
    ]


def swing_lows(candles: list[Candle], lookback: int = 2) -> list[int]:
    return [
        index
        for index in range(lookback, len(candles) - lookback)
        if candles[index].low == min(candle.low for candle in candles[index - lookback : index + lookback + 1])
    ]
