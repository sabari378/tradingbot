"""Strategy-specific demo exits; all inputs must be completed candles."""

import json
import math
from statistics import fmean

from nirv.market.candles import swing_highs, swing_lows
from nirv.strategies.catalog import _atr

TREND = frozenset(("sma_crossover", "donchian_breakout", "volatility_breakout", "market_structure"))
MEAN = frozenset(("bollinger_reversion", "rsi_countertrend"))
REVERSAL = frozenset(("liquidity_sweep", "fair_value_gap", "engulfing_reversal", "double_top"))
POLICY = "adaptive_v1"


def exit_target(strategy, candles, direction, entry):
    """Return a fixed entry-time target or zero for an ATR trailing exit.

    No valid opposing level means reject a new entry / retain an existing exit.
    """
    if len(candles) < 21 or direction not in ("BUY", "SELL"):
        raise ValueError("adaptive_exit_insufficient_data")
    if strategy in TREND:
        return 0.0, "atr_trail_2_after_1R"
    if strategy in MEAN:
        target = fmean(c.close for c in candles[-20:])
        rule = "entry_sma20"
    elif strategy in REVERSAL:
        indices = swing_highs(candles) if direction == "BUY" else swing_lows(candles)
        levels = [candles[i].high if direction == "BUY" else candles[i].low for i in indices]
        levels = [p for p in levels if p > entry] if direction == "BUY" else [p for p in levels if p < entry]
        if not levels:
            raise ValueError("adaptive_exit_no_opposing_swing")
        target = min(levels) if direction == "BUY" else max(levels)
        rule = "nearest_confirmed_opposing_swing"
    else:
        raise ValueError("adaptive_exit_unknown_strategy")
    if not math.isfinite(target) or (target <= entry if direction == "BUY" else target >= entry):
        raise ValueError("adaptive_exit_target_not_profitable")
    return target, rule


def round_target(target, info):
    return round(round(target / info.trade_tick_size) * info.trade_tick_size, info.digits) if target else 0.0


def trailing_stop(candles, direction, entry, initial_stop, current_stop, bid, ask, info, protect_profit=False):
    """Activate at +1 initial R; trail completed close by 2 ATR, never loosen."""
    risk = abs(entry - initial_stop)
    quote = bid if direction == "BUY" else ask
    gain = quote - entry if direction == "BUY" else entry - quote
    if risk <= 0 or gain < risk:
        return current_stop
    atr = _atr(candles)
    if not math.isfinite(atr) or atr <= 0:
        return current_stop
    candidate = candles[-1].close + (-2 * atr if direction == "BUY" else 2 * atr)
    if protect_profit:
        # Gross entry plus current spread; commissions/slippage can still produce a small loss.
        floor = entry + (ask - bid if direction == "BUY" else -(ask - bid))
        candidate = max(candidate, floor) if direction == "BUY" else min(candidate, floor)
    step = info.trade_tick_size
    candidate = (math.floor(candidate / step) if direction == "BUY" else math.ceil(candidate / step)) * step
    candidate = round(candidate, info.digits)
    if direction == "BUY":
        return max(current_stop, initial_stop, candidate)
    return min(current_stop, initial_stop, candidate)


def valid_levels(direction, stop, target, tick, info):
    """Respect both broker stop/freeze distances before an order or amendment."""
    if stop <= 0 or not all(math.isfinite(x) for x in (stop, target, tick.bid, tick.ask)):
        return False
    gap = max(info.trade_stops_level, info.trade_freeze_level) * info.point + info.trade_tick_size
    if direction == "BUY":
        return tick.bid - stop >= gap and (target == 0 or target - tick.bid >= gap)
    return stop - tick.ask >= gap and (target == 0 or tick.ask - target >= gap)


def manage_exits(mt5, journals, symbol, emit, authorize, policy=POLICY, protect_profit=False):
    """Manage only tickets recorded in this session, with matching magic/symbol.

    Rebuild plans from entry-time candles after restart; broker is the source of
    truth for stop tightening. Existing targets remain if migration is invalid.
    """
    from datetime import datetime, timezone

    from nirv.market.candles import Candle

    positions = mt5.positions_get()
    if positions is None:
        raise ValueError("adaptive_exit_positions_unavailable")
    active = {p.ticket: p for p in positions}
    info = mt5.symbol_info(symbol)
    if info is None:
        raise ValueError("adaptive_exit_symbol_unavailable")
    for strategy, path in journals.items():
        intents, fills, plans, applied, retained = {}, {}, {}, set(), set()
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row["event"] == "ORDER_INTENT":
                intents[row["timeframe"]] = row
            elif row["event"] == "FILLED":
                fills[int(row["ticket"])] = (row, intents.get(row["timeframe"]))
            elif row["event"] == "EXIT_PLAN":
                plans[int(row["ticket"])] = row
            elif row["event"] == "EXIT_POLICY_RETAINED":
                retained.add(int(row["ticket"]))
            elif row["event"] == "EXIT_POLICY_APPLIED":
                applied.add(int(row["ticket"]))
        for ticket, (fill, intent) in fills.items():
            if ticket in retained:
                continue
            p = active.get(ticket)
            if p is None or p.symbol != symbol or p.magic != fill["magic"]:
                continue
            try:
                tf = getattr(mt5, "TIMEFRAME_" + fill["timeframe"])
                direction = fill["direction"]
                if ticket not in plans:
                    if intent is None:
                        raise ValueError("adaptive_exit_missing_entry_snapshot")
                    cutoff = int(intent["signal_key"].split(":")[1])
                    rates = mt5.copy_rates_from(symbol, tf, datetime.fromtimestamp(cutoff, timezone.utc), 200)
                    if rates is None or len(rates) < 51 or int(rates[-1]["time"]) != cutoff:
                        raise ValueError("adaptive_exit_entry_history_unavailable")
                    candles = [
                        Candle(float(b["open"]), float(b["high"]), float(b["low"]), float(b["close"])) for b in rates
                    ]
                    target, rule = exit_target(strategy, candles, direction, fill["entry"])
                    plan = dict(
                        ticket=ticket,
                        policy=POLICY,
                        target=round_target(target, info),
                        rule=rule,
                        source_signal=intent["signal_key"],
                        initial_stop=fill["stop_loss"],
                        original_target=fill["take_profit"],
                    )
                    emit(path, "EXIT_PLAN", **plan)
                    plans[ticket] = plan
                plan = plans[ticket]
                target = plan["target"]
                stop = p.sl
                if not stop:
                    raise ValueError("adaptive_exit_missing_protective_stop")
                tick = mt5.symbol_info_tick(symbol)
                if tick is None:
                    raise ValueError("adaptive_exit_quote_unavailable")
                if target and (target <= tick.bid if direction == "BUY" else target >= tick.ask):
                    emit(
                        path,
                        "EXIT_POLICY_RETAINED",
                        ticket=ticket,
                        policy="fixed_2R",
                        reason="entry_target_already_passed_at_migration",
                        stop_loss=p.sl,
                        take_profit=p.tp,
                    )
                    continue
                if strategy in TREND:
                    rates = mt5.copy_rates_from_pos(symbol, tf, 1, 200)
                    if rates is None or len(rates) < 51:
                        raise ValueError("adaptive_exit_trailing_history_unavailable")
                    candles = [
                        Candle(float(b["open"]), float(b["high"]), float(b["low"]), float(b["close"])) for b in rates
                    ]
                    stop = trailing_stop(
                        candles,
                        direction,
                        fill["entry"],
                        plan["initial_stop"],
                        p.sl,
                        tick.bid,
                        tick.ask,
                        info,
                        protect_profit=protect_profit,
                    )
                if abs(stop - p.sl) < info.trade_tick_size / 2 and abs(target - p.tp) < info.trade_tick_size / 2:
                    if ticket not in applied:
                        emit(
                            path,
                            "EXIT_POLICY_APPLIED",
                            ticket=ticket,
                            policy=POLICY,
                            stop_loss=p.sl,
                            take_profit=p.tp,
                            reconciled=True,
                        )
                    continue
                if not valid_levels(direction, stop, target, tick, info):
                    raise ValueError("adaptive_exit_broker_distance_or_target_already_passed")
                # Recheck account, emergency stop and cutoff immediately before mutation.
                if not authorize():
                    continue
                current = mt5.positions_get(ticket=ticket)
                if not current:
                    continue
                p = current[0]
                if p.symbol != symbol or p.magic != fill["magic"]:
                    continue
                stop = max(stop, p.sl) if direction == "BUY" else min(stop, p.sl)
                latest_tick = mt5.symbol_info_tick(symbol)
                if not p.sl or latest_tick is None or not valid_levels(direction, stop, target, latest_tick, info):
                    continue
                request = dict(action=mt5.TRADE_ACTION_SLTP, position=ticket, symbol=symbol, sl=stop, tp=target)
                checked = mt5.order_check(request)
                if checked is None or checked.retcode != 0:
                    raise ValueError("adaptive_exit_order_check_failed")
                emit(
                    path, "EXIT_MODIFY_INTENT", ticket=ticket, policy=POLICY, old_sl=p.sl, old_tp=p.tp, request=request
                )
                result = mt5.order_send(request)
                if result is None or result.retcode not in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_NO_CHANGES):
                    emit(
                        path,
                        "EXIT_MODIFY_UNCONFIRMED",
                        ticket=ticket,
                        retcode=getattr(result, "retcode", None),
                        reason=getattr(result, "comment", "no_response"),
                    )
                    continue  # Reconcile actual levels before any retry on next poll.
                confirmed = mt5.positions_get(ticket=ticket)
                if (
                    confirmed
                    and abs(confirmed[0].sl - stop) < info.trade_tick_size / 2
                    and abs(confirmed[0].tp - target) < info.trade_tick_size / 2
                ):
                    emit(
                        path,
                        "EXIT_POLICY_APPLIED",
                        ticket=ticket,
                        policy=POLICY,
                        stop_loss=confirmed[0].sl,
                        take_profit=confirmed[0].tp,
                        rule=plan["rule"],
                    )
            except ValueError as error:
                emit(path, "EXIT_DEFERRED", ticket=ticket, reason=str(error))
