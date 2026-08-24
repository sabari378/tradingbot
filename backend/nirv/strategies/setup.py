from dataclasses import dataclass

from nirv.market.candles import Candle

from .confluence import ConfluenceDecision, evaluate_confluence
from .fair_value_gap import fair_value_gaps
from .liquidity_sweep import liquidity_sweep
from .market_structure import detect_mss


@dataclass(frozen=True)
class SetupDecision:
    confluence: ConfluenceDecision
    entry: float | None
    stop_loss: float | None
    take_profit: float | None
    volume_confirmed: bool


def analyze_setup(
    candles: list[Candle],
    *,
    lookback: int = 2,
    liquidity_lookback: int = 20,
    volume_window: int = 20,
    volume_multiplier: float = 1.2,
    risk_reward: float = 2.0,
    news_blocked: bool = False,
) -> SetupDecision:
    if len(candles) < max(lookback + 2, liquidity_lookback + 1, volume_window + 1, 3):
        return SetupDecision(
            confluence=evaluate_confluence(
                sweep=None, mss=None, fvg=None, volume_confirmed=False, news_blocked=news_blocked
            ),
            entry=None,
            stop_loss=None,
            take_profit=None,
            volume_confirmed=False,
        )

    current = candles[-1]
    history = candles[-liquidity_lookback - 1 : -1]
    buy_side_level = max(candle.high for candle in history)
    sell_side_level = min(candle.low for candle in history)
    sweep = None
    if liquidity_sweep(candles, "buy_side", buy_side_level):
        sweep = "buy_side"
    elif liquidity_sweep(candles, "sell_side", sell_side_level):
        sweep = "sell_side"

    gaps = fair_value_gaps(candles)
    latest_gap = gaps[-1] if gaps else None
    fvg = latest_gap["direction"] if latest_gap else None
    average_volume = sum(candle.volume for candle in candles[-volume_window - 1 : -1]) / volume_window
    volume_confirmed = average_volume > 0 and current.volume >= average_volume * volume_multiplier
    mss = detect_mss(candles, lookback)
    confluence = evaluate_confluence(
        sweep=sweep,
        mss=mss,
        fvg=fvg,
        volume_confirmed=volume_confirmed,
        news_blocked=news_blocked,
    )
    if not confluence.direction:
        return SetupDecision(confluence, None, None, None, volume_confirmed)

    entry = current.close
    stop_loss = current.high if confluence.direction == "SELL" else current.low
    target_distance = abs(entry - stop_loss) * risk_reward
    take_profit = entry - target_distance if confluence.direction == "SELL" else entry + target_distance
    return SetupDecision(confluence, entry, stop_loss, take_profit, volume_confirmed)