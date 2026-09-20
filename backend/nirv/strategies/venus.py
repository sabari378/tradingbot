from nirv.market.candles import Candle, swing_highs, swing_lows


def target_before_opposing_structure(
    candles: list[Candle],
    direction: str,
    entry: float,
    stop_loss: float,
    *,
    desired_risk_reward: float = 2.0,
    buffer_atr: float = 0.1,
) -> tuple[float, float]:
    """Return a target capped just before the first confirmed opposing swing."""
    risk = abs(entry - stop_loss)
    if risk <= 0:
        raise ValueError("entry and stop loss must differ")
    history = candles[:-1]
    average_range = sum(candle.high - candle.low for candle in candles[-15:]) / min(15, len(candles))
    buffer = average_range * buffer_atr

    if direction == "BUY":
        desired = entry + risk * desired_risk_reward
        resistances = sorted(
            candles[index].high
            for index in swing_highs(history, 2)
            if entry < candles[index].high <= desired
        )
        target = resistances[0] - buffer if resistances else desired
    elif direction == "SELL":
        desired = entry - risk * desired_risk_reward
        supports = sorted(
            (
                candles[index].low
                for index in swing_lows(history, 2)
                if desired <= candles[index].low < entry
            ),
            reverse=True,
        )
        target = supports[0] + buffer if supports else desired
    else:
        raise ValueError(f"unsupported direction: {direction}")

    reward = abs(target - entry)
    return target, reward / risk


def reached_one_r(direction: str, entry: float, initial_stop: float, current_price: float) -> bool:
    risk = abs(entry - initial_stop)
    return current_price >= entry + risk if direction == "BUY" else current_price <= entry - risk
