"""Explicit experiment risk limits, independent of historical strategy rankings."""

import math

from nirv.strategies.adaptive_exits import TREND
from nirv.strategies.catalog import CATALOG_STRATEGIES

MAGIC_BASE = 1302020000


def catalog_strategy(magic):
    index, timeframe = divmod(magic - MAGIC_BASE, 10)
    return CATALOG_STRATEGIES[index] if 0 <= index < len(CATALOG_STRATEGIES) and timeframe < 3 else None


def check_overlap(positions, strategy, symbol, side, magic):
    for p in positions:
        if p.symbol != symbol:
            continue
        if p.magic == magic:
            raise ValueError("guard_existing_strategy_timeframe_position")
        if strategy in TREND and p.type == side and catalog_strategy(p.magic) in TREND:
            raise ValueError("guard_overlapping_trend_direction")


def equity_at_risk(mt5, positions):
    """Account-currency loss from current mark to stop, including profit giveback."""
    total = 0.0
    for p in positions:
        if not p.sl or not math.isfinite(p.price_current) or p.price_current <= 0:
            return math.inf
        pnl = mt5.order_calc_profit(p.type, p.symbol, p.volume, p.price_current, p.sl)
        if pnl is None or not math.isfinite(pnl):
            return math.inf
        total += max(0, -pnl)
    return total


def entry_budget(mt5, positions, equity, start_equity, per_trade=0.0025, total=0.01, loss_limit=0.01):
    if not all(math.isfinite(v) and v > 0 for v in (equity, start_equity)):
        raise ValueError("guard_invalid_equity")
    if equity <= start_equity * (1 - loss_limit):
        raise ValueError("guard_session_equity_loss_limit")
    capacity = equity * total - equity_at_risk(mt5, positions)
    # Leave room for all existing stop losses plus this trade before the session-loss threshold.
    loss_capacity = equity - start_equity * (1 - loss_limit) - equity_at_risk(mt5, positions)
    budget = min(equity * per_trade, capacity, loss_capacity)
    if budget <= 0:
        raise ValueError("guard_account_risk_budget_exhausted")
    return budget


def check_target_reward(direction, entry, stop, target, min_r=1.0):
    if target == 0:
        return  # Trend trades use a trailing exit.
    risk = entry - stop if direction == "BUY" else stop - entry
    reward = target - entry if direction == "BUY" else entry - target
    if risk <= 0 or not math.isfinite(reward) or reward < risk * min_r:
        raise ValueError("guard_target_below_1R")
