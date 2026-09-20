from statistics import fmean, pstdev

from nirv.market.candles import Candle
from nirv.strategies.confluence import ConfluenceDecision
from nirv.strategies.double_top import analyze_double_top_displacement
from nirv.strategies.market_structure import detect_bos, fresh_bos_context
from nirv.strategies.setup import SetupDecision, analyze_setup

CATALOG_STRATEGIES = (
    "sma_crossover",
    "donchian_breakout",
    "bollinger_reversion",
    "rsi_countertrend",
    "volatility_breakout",
    "engulfing_reversal",
    "market_structure",
    "liquidity_sweep",
    "fair_value_gap",
    "double_top",
)


def evaluate_catalog_strategy(
    name: str, candles: list[Candle], *, risk_reward: float, require_volume: bool = False, fresh_structure: bool = False
) -> SetupDecision:
    if name == "liquidity_sweep":
        return analyze_setup(
            candles,
            news_blocked=False,
            risk_reward=risk_reward,
            use_liquidity=True,
            use_mss=False,
            use_fvg=False,
            use_volume=require_volume,
            require_volume=require_volume,
            stop_method="structure",
        )
    if name == "fair_value_gap":
        return analyze_setup(
            candles,
            news_blocked=False,
            risk_reward=risk_reward,
            use_liquidity=False,
            use_mss=False,
            use_fvg=True,
            use_volume=require_volume,
            require_volume=require_volume,
            stop_method="structure",
        )
    if len(candles) < 25:
        return _none()

    volume_confirmed = _volume_confirmed(candles)
    if require_volume and not volume_confirmed:
        return _none(volume_confirmed)

    direction: str | None = None
    label = name
    atr = _atr(candles)
    current = candles[-1]

    if name == "sma_crossover":
        if len(candles) < 51:
            return _none(volume_confirmed)
        fast, slow = fmean(c.close for c in candles[-20:]), fmean(c.close for c in candles[-50:])
        prior_fast = fmean(c.close for c in candles[-21:-1])
        prior_slow = fmean(c.close for c in candles[-51:-1])
        direction = (
            "BUY"
            if prior_fast <= prior_slow and fast > slow
            else "SELL"
            if prior_fast >= prior_slow and fast < slow
            else None
        )
    elif name == "donchian_breakout":
        prior = candles[-21:-1]
        direction = (
            "BUY"
            if current.close > max(c.high for c in prior)
            else "SELL"
            if current.close < min(c.low for c in prior)
            else None
        )
    elif name == "bollinger_reversion":
        closes = [c.close for c in candles[-20:]]
        prior_closes = [c.close for c in candles[-21:-1]]
        mean, deviation = fmean(closes), pstdev(closes)
        prior_mean, prior_deviation = fmean(prior_closes), pstdev(prior_closes)
        if deviation > 0 and prior_deviation > 0:
            z_score = (current.close - mean) / deviation
            prior_z = (candles[-2].close - prior_mean) / prior_deviation
            direction = "BUY" if prior_z >= -2 and z_score < -2 else "SELL" if prior_z <= 2 and z_score > 2 else None
    elif name == "rsi_countertrend":
        prior_rsi, current_rsi = _rsi(candles[:-1]), _rsi(candles)
        direction = "BUY" if prior_rsi <= 30 < current_rsi else "SELL" if prior_rsi >= 70 > current_rsi else None
    elif name == "volatility_breakout":
        prior = candles[-21:-1]
        expanded = current.high - current.low >= atr * 1.5
        if expanded:
            direction = (
                "BUY"
                if current.close > max(c.high for c in prior)
                else "SELL"
                if current.close < min(c.low for c in prior)
                else None
            )
    elif name == "engulfing_reversal":
        previous = candles[-2]
        bullish = (
            previous.bearish and current.bullish and current.open <= previous.close and current.close >= previous.open
        )
        bearish = (
            previous.bullish and current.bearish and current.open >= previous.close and current.close <= previous.open
        )
        direction = "BUY" if bullish else "SELL" if bearish else None
    elif name == "market_structure":
        structure = fresh_bos_context(candles)["direction"] if fresh_structure else detect_bos(candles)
        direction = "BUY" if structure == "bullish" else "SELL" if structure == "bearish" else None
    elif name == "double_top":
        setup = analyze_double_top_displacement(candles)
        if setup.direction and setup.stop_loss is not None:
            return _decision(
                setup.direction, current.close, setup.stop_loss, risk_reward, setup.reasons, volume_confirmed
            )
        return _none(volume_confirmed)
    else:
        raise ValueError(f"unknown catalog strategy: {name}")

    if direction is None:
        return _none(volume_confirmed)
    stop = current.close - atr * 1.5 if direction == "BUY" else current.close + atr * 1.5
    return _decision(direction, current.close, stop, risk_reward, [label], volume_confirmed)


def _decision(
    direction: str,
    entry: float,
    stop: float,
    risk_reward: float,
    labels: list[str],
    volume_confirmed: bool,
) -> SetupDecision:
    distance = abs(entry - stop)
    target = entry + distance * risk_reward if direction == "BUY" else entry - distance * risk_reward
    confluences = labels + (["volume_confirmation"] if volume_confirmed else [])
    return SetupDecision(
        ConfluenceDecision(direction, confluences, len(confluences)), entry, stop, target, volume_confirmed
    )


def _none(volume_confirmed: bool = False) -> SetupDecision:
    return SetupDecision(ConfluenceDecision(None, [], 0), None, None, None, volume_confirmed)


def _atr(candles: list[Candle], period: int = 14) -> float:
    sample = candles[-(period + 1) :]
    ranges = [
        max(
            candle.high - candle.low,
            abs(candle.high - sample[index - 1].close),
            abs(candle.low - sample[index - 1].close),
        )
        for index, candle in enumerate(sample[1:], start=1)
    ]
    return fmean(ranges)


def _rsi(candles: list[Candle], period: int = 14) -> float:
    changes = [candles[index].close - candles[index - 1].close for index in range(len(candles) - period, len(candles))]
    gains = fmean(max(change, 0) for change in changes)
    losses = fmean(max(-change, 0) for change in changes)
    if losses == 0:
        return 100
    return 100 - 100 / (1 + gains / losses)


def _volume_confirmed(candles: list[Candle]) -> bool:
    baseline = fmean(candle.volume for candle in candles[-21:-1])
    return baseline > 0 and candles[-1].volume >= baseline * 1.2


def evaluate_pluto4_strategy(name: str, candles: list[Candle], *, risk_reward: float) -> SetupDecision:
    """Pluto 3 baseline plus two explicit reversal-quality filters."""
    baseline = evaluate_catalog_strategy(name, candles, risk_reward=risk_reward,
                                         fresh_structure=name == "market_structure")
    direction = baseline.confluence.direction
    if direction is None or name not in ("liquidity_sweep", "engulfing_reversal"):
        return baseline
    current = candles[-1]
    if name == "liquidity_sweep":
        span = current.high - current.low
        accepted = span > 0 and (
            current.bullish and current.close >= current.low + span * 2 / 3
            if direction == "BUY" else
            current.bearish and current.close <= current.low + span / 3
        )
        label = "directional_close_outer_third"
    else:
        prior = candles[-21:-1]
        accepted = (
            min(current.low, candles[-2].low) <= min(c.low for c in prior)
            if direction == "BUY" else
            max(current.high, candles[-2].high) >= max(c.high for c in prior)
        )
        label = "engulfing_at_20_bar_extreme"
    if not accepted:
        return SetupDecision(ConfluenceDecision(None, ["filtered:" + label], 0),
                             None, None, None, baseline.volume_confirmed)
    return SetupDecision(ConfluenceDecision(direction, baseline.confluence.confluences + [label],
                                            baseline.confluence.score + 1),
                         baseline.entry, baseline.stop_loss, baseline.take_profit, baseline.volume_confirmed)
