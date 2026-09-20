from dataclasses import dataclass

from nirv.market.candles import Candle, swing_highs, swing_lows

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
    use_liquidity: bool = True,
    use_mss: bool = True,
    use_fvg: bool = True,
    use_volume: bool = True,
    require_volume: bool = False,
    stop_method: str = "candle",
    stop_buffer_atr: float = 0.1,
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
    if use_liquidity:
        if liquidity_sweep(candles, "buy_side", buy_side_level):
            sweep = "buy_side"
        elif liquidity_sweep(candles, "sell_side", sell_side_level):
            sweep = "sell_side"

    # A gap is a trigger only on the candle that creates it, not forever after it appears in history.
    gaps = fair_value_gaps(candles[-3:])
    latest_gap = gaps[-1] if gaps else None
    fvg = latest_gap["direction"] if latest_gap and use_fvg else None
    average_volume = sum(candle.volume for candle in candles[-volume_window - 1 : -1]) / volume_window
    volume_confirmed = average_volume > 0 and current.volume >= average_volume * volume_multiplier
    mss = detect_mss(candles, lookback) if use_mss else None
    confluence = evaluate_confluence(
        sweep=sweep,
        mss=mss,
        fvg=fvg,
        volume_confirmed=volume_confirmed if use_volume else False,
        news_blocked=news_blocked,
    )
    if require_volume and not volume_confirmed:
        confluence = ConfluenceDecision(None, confluence.confluences, confluence.score)
    if not confluence.direction:
        return SetupDecision(confluence, None, None, None, volume_confirmed)

    entry = current.close
    if stop_method == "structure":
        true_ranges = [
            max(candles[index].high - candles[index].low,
                abs(candles[index].high - candles[index - 1].close),
                abs(candles[index].low - candles[index - 1].close))
            for index in range(max(1, len(candles) - 15), len(candles))
        ]
        buffer = (sum(true_ranges) / len(true_ranges)) * stop_buffer_atr
        if confluence.direction == "BUY":
            pivots = swing_lows(candles[:-1], lookback)
            # Include later extremes: a swept pivot is not an intact stop anchor.
            leg = candles[pivots[-1]:] if pivots else [*history, current]
            zone = min(candle.low for candle in leg)
            stop_loss = zone - buffer
        else:
            pivots = swing_highs(candles[:-1], lookback)
            leg = candles[pivots[-1]:] if pivots else [*history, current]
            zone = max(candle.high for candle in leg)
            stop_loss = zone + buffer
    else:
        stop_loss = current.high if confluence.direction == "SELL" else current.low
    if (confluence.direction == "BUY" and stop_loss >= entry) or (
        confluence.direction == "SELL" and stop_loss <= entry
    ):
        return SetupDecision(
            ConfluenceDecision(None, confluence.confluences, confluence.score), None, None, None, volume_confirmed
        )
    target_distance = abs(entry - stop_loss) * risk_reward
    take_profit = entry - target_distance if confluence.direction == "SELL" else entry + target_distance
    return SetupDecision(confluence, entry, stop_loss, take_profit, volume_confirmed)
