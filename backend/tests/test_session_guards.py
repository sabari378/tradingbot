from types import SimpleNamespace as NS

import pytest

from nirv.strategies.session_guards import check_overlap, check_target_reward, entry_budget, equity_at_risk


def broker():
    return NS(
        order_calc_profit=lambda side, symbol, volume, entry, stop: (
            (stop - entry if side == 0 else entry - stop) * 100 * volume
        )
    )


def position(**fields):
    return NS(
        **(
            dict(symbol="GOLD", type=0, magic=1302020010, sl=95, price_open=100, price_current=105, volume=0.01)
            | fields
        )
    )


def test_duplicate_strategy_and_correlated_trends_are_blocked():
    with pytest.raises(ValueError, match="strategy_timeframe"):
        check_overlap([position()], "donchian_breakout", "GOLD", 0, 1302020010)
    with pytest.raises(ValueError, match="overlapping_trend"):
        check_overlap([position()], "volatility_breakout", "GOLD", 0, 1302020041)
    check_overlap([position()], "volatility_breakout", "GOLD", 1, 1302020041)
    check_overlap([position()], "fair_value_gap", "GOLD", 0, 1302020080)
    check_overlap([position(symbol="OTHER")], "volatility_breakout", "GOLD", 0, 1302020040)


def test_equity_risk_includes_profit_giveback_and_foreign_positions():
    assert equity_at_risk(broker(), [position(sl=101)]) == 4
    assert equity_at_risk(broker(), [position(), position(magic=999)]) == 20
    assert equity_at_risk(broker(), [position(sl=0)]) == float("inf")
    assert equity_at_risk(NS(order_calc_profit=lambda *args: None), [position()]) == float("inf")


def test_budget_caps_trade_total_and_remaining_session_loss_room():
    assert entry_budget(broker(), [], 10000, 10000) == 25
    assert entry_budget(broker(), [position(volume=0.095)], 10000, 10000) == pytest.approx(5)
    assert entry_budget(broker(), [], 9910, 10000) == 10
    with pytest.raises(ValueError, match="session_equity_loss"):
        entry_budget(broker(), [], 9900, 10000)
    with pytest.raises(ValueError, match="budget_exhausted"):
        entry_budget(broker(), [position(sl=0)], 10000, 10000)


@pytest.mark.parametrize("direction,entry,stop,target", [("BUY", 100, 90, 105), ("SELL", 100, 110, 95)])
def test_reject_small_targets_without_widening_them(direction, entry, stop, target):
    with pytest.raises(ValueError, match="below_1R"):
        check_target_reward(direction, entry, stop, target)
    check_target_reward(direction, entry, stop, 0)


def test_one_r_targets_pass():
    check_target_reward("BUY", 100, 90, 110)
    check_target_reward("SELL", 100, 110, 90)
