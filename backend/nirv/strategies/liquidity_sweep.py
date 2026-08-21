from nirv.market.candles import Candle


def equal_highs(candles: list[Candle], tolerance: float = 0.05) -> bool:
    return len(candles) >= 2 and abs(candles[-1].high - candles[-2].high) <= tolerance


def equal_lows(candles: list[Candle], tolerance: float = 0.05) -> bool:
    return len(candles) >= 2 and abs(candles[-1].low - candles[-2].low) <= tolerance


def liquidity_sweep(candles: list[Candle], side: str, level: float) -> bool:
    if not candles:
        return False
    candle = candles[-1]
    return (
        candle.high > level and candle.close < level
        if side == "buy_side"
        else candle.low < level and candle.close > level
    )
