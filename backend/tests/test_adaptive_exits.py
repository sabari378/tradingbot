from types import SimpleNamespace

import pytest

from nirv.market.candles import Candle
from nirv.strategies.adaptive_exits import exit_target, trailing_stop, valid_levels


def history():
    bars = [Candle(100, 101, 99, 100) for _ in range(25)]
    bars[10] = Candle(100, 110, 98, 100)
    bars[18] = Candle(100, 106, 90, 100)
    return bars


def info():
    return SimpleNamespace(trade_tick_size=0.01, digits=2, trade_stops_level=10, trade_freeze_level=20, point=0.01)


def test_nearest_confirmed_opposing_swing_both_sides():
    assert exit_target("fair_value_gap", history(), "BUY", 102)[0] == 106
    assert exit_target("liquidity_sweep", history(), "SELL", 97)[0] == 90


def test_no_profitable_swing_rejects_instead_of_fabricating_target():
    with pytest.raises(ValueError, match="no_opposing_swing"):
        exit_target("double_top", history(), "BUY", 111)


def test_unconfirmed_latest_high_is_not_a_target():
    bars = history()
    bars[-1] = Candle(100, 120, 99, 100)
    with pytest.raises(ValueError, match="no_opposing_swing"):
        exit_target("engulfing_reversal", bars, "BUY", 111)


def test_mean_target_must_be_profitable():
    assert exit_target("rsi_countertrend", history(), "BUY", 95)[0] == 100
    with pytest.raises(ValueError, match="not_profitable"):
        exit_target("bollinger_reversion", history(), "BUY", 105)


@pytest.mark.parametrize("strategy", ["sma_crossover", "donchian_breakout", "volatility_breakout", "market_structure"])
def test_trend_has_no_fixed_target(strategy):
    assert exit_target(strategy, history(), "BUY", 100)[0] == 0


def test_trailing_waits_for_one_r_and_never_loosens():
    assert trailing_stop(history(), "BUY", 100, 90, 90, 109, 109.1, info()) == 90
    assert trailing_stop(history(), "BUY", 100, 90, 99, 112, 112.1, info()) == 99
    assert trailing_stop(history(), "SELL", 100, 110, 101, 87.9, 88, info()) == 101


def test_trailing_tightens_buy_and_sell():
    assert trailing_stop(history(), "BUY", 90, 80, 80, 110, 110.1, info()) > 80
    assert trailing_stop(history(), "SELL", 110, 120, 120, 89.9, 90, info()) < 120


def test_broker_freeze_and_crossed_targets_are_rejected():
    tick = SimpleNamespace(bid=100, ask=100.1)
    assert valid_levels("BUY", 99, 101, tick, info())
    assert not valid_levels("BUY", 99.9, 101, tick, info())
    assert not valid_levels("BUY", 99, 99.5, tick, info())
    assert valid_levels("SELL", 101, 0, tick, info())
    assert not valid_levels("SELL", 100.2, 99, tick, info())


def test_manager_respects_authorization_and_never_touches_foreign_tickets(tmp_path):
    import json

    from nirv.strategies.adaptive_exits import manage_exits

    path = tmp_path / "fair_value_gap-demo.jsonl"
    rows = [
        dict(
            event="FILLED",
            ticket=7,
            timeframe="M15",
            direction="BUY",
            entry=100,
            stop_loss=90,
            take_profit=120,
            magic=123,
        ),
        dict(event="EXIT_PLAN", ticket=7, target=110, initial_stop=90, rule="test"),
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    p = SimpleNamespace(ticket=7, symbol="GOLD.i#", magic=123, sl=90, tp=120)

    class Broker:
        TIMEFRAME_M15 = 15
        TRADE_ACTION_SLTP = 6
        TRADE_RETCODE_DONE = 10009
        TRADE_RETCODE_NO_CHANGES = 10025
        sends = 0

        def positions_get(self, **kwargs):
            return [p]

        def symbol_info(self, symbol):
            return info()

        def symbol_info_tick(self, symbol):
            return SimpleNamespace(bid=105, ask=105.1)

        def order_check(self, request):
            return SimpleNamespace(retcode=0)

        def order_send(self, request):
            self.sends += 1
            p.sl, p.tp = request["sl"], request["tp"]
            return SimpleNamespace(retcode=self.TRADE_RETCODE_DONE)

    broker = Broker()
    events = []

    def emit(path, event, **fields):
        events.append((event, fields))

    manage_exits(broker, {"fair_value_gap": path}, "GOLD.i#", emit, lambda: False)
    assert broker.sends == 0
    p.magic = 999
    manage_exits(broker, {"fair_value_gap": path}, "GOLD.i#", emit, lambda: True)
    assert broker.sends == 0
    p.magic = 123
    manage_exits(broker, {"fair_value_gap": path}, "GOLD.i#", emit, lambda: True)
    assert broker.sends == 1
    assert p.sl == 90 and p.tp == 110
    assert events[-1][0] == "EXIT_POLICY_APPLIED"


def test_manager_retains_original_exit_if_target_already_passed(tmp_path):
    import json

    from nirv.strategies.adaptive_exits import manage_exits

    path = tmp_path / "fair_value_gap-demo.jsonl"
    rows = [
        dict(
            event="FILLED",
            ticket=7,
            timeframe="M15",
            direction="BUY",
            entry=100,
            stop_loss=90,
            take_profit=120,
            magic=123,
        ),
        dict(event="EXIT_PLAN", ticket=7, target=104, initial_stop=90, rule="test"),
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    p = SimpleNamespace(ticket=7, symbol="GOLD.i#", magic=123, sl=90, tp=120)
    broker = SimpleNamespace(
        positions_get=lambda: [p],
        symbol_info=lambda s: info(),
        TIMEFRAME_M15=15,
        symbol_info_tick=lambda s: SimpleNamespace(bid=105, ask=105.1),
    )
    events = []
    manage_exits(
        broker, {"fair_value_gap": path}, "GOLD.i#", lambda path, event, **fields: events.append(event), lambda: True
    )
    assert events == ["EXIT_POLICY_RETAINED"]
    assert p.sl == 90 and p.tp == 120


def test_guarded_profit_floor_at_one_r_and_no_widening():
    assert trailing_stop(history(), "BUY", 100, 90, 90, 110, 110.1, info(), protect_profit=True) == 100.1
    assert trailing_stop(history(), "SELL", 100, 110, 110, 89.9, 90, info(), protect_profit=True) == 99.9
    assert trailing_stop(history(), "BUY", 100, 90, 103, 109, 109.1, info(), protect_profit=True) == 103
