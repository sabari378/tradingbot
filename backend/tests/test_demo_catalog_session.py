import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

spec = importlib.util.spec_from_file_location('catalog_runner', Path(__file__).parents[1] / 'demo_catalog_session.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_minimum_lot_is_rejected_without_moving_stop():
    broker = NS(order_calc_profit=lambda side, symbol, volume, entry, stop: -volume * 100 * abs(entry-stop))
    info = NS(volume_min=.01, volume_max=50, volume_step=.01)
    with pytest.raises(ValueError, match='minimum_lot'):
        runner.select_volume(broker, 'GOLD', 0, 100, 90, info, 5)
    volume, loss = runner.select_volume(broker, 'GOLD', 0, 100, 90, info, 25)
    assert volume == .02
    assert loss == 20


def test_risk_includes_every_position_and_missing_stop_blocks_budget():
    broker = NS(order_calc_profit=lambda side, symbol, volume, entry, stop: (stop-entry)*volume*100)
    p = NS(type=0, symbol='GOLD', volume=.01, price_open=100, sl=95)
    assert runner.open_risk(broker, [p, p]) == 10
    p.sl = 0
    assert runner.open_risk(broker, [p]) == float('inf')


@pytest.mark.parametrize('mode', [0, 2])
def test_non_demo_account_rejected(mode):
    broker = NS(account_info=lambda: NS(trade_mode=mode), terminal_info=lambda: NS(connected=True),
                ACCOUNT_TRADE_MODE_DEMO=1)
    with pytest.raises(ValueError, match='demo_account'):
        runner.check_account(broker)


@pytest.mark.parametrize("variant", ["pluto", "pluto3", "pluto4"])
@pytest.mark.parametrize("disabled", [None, "market_structure"])
def test_ten_sessions_three_timeframes_deduplicate_and_stop(tmp_path, monkeypatch, disabled, variant):
    monkeypatch.setattr(runner, "strategy_enabled", lambda strategy: strategy != disabled)
    clock = [1000.0]
    orders = []
    timeframe_calls = []
    info = NS(visible=True, volume_min=.01, volume_max=50, volume_step=.01, trade_tick_size=.01, digits=2)
    class Broker:
        ACCOUNT_TRADE_MODE_DEMO=1
        ACCOUNT_MARGIN_MODE_RETAIL_HEDGING=2
        TIMEFRAME_M15=15; TIMEFRAME_M30=30; TIMEFRAME_H1=60
        ORDER_TYPE_BUY=0; ORDER_TYPE_SELL=1
        TRADE_ACTION_DEAL=1; ORDER_TIME_GTC=0; ORDER_FILLING_IOC=1
        TRADE_RETCODE_TIMEOUT=10; TRADE_RETCODE_CONNECTION=11
        TRADE_RETCODE_DONE=12; TRADE_RETCODE_DONE_PARTIAL=13
        def initialize(self, **kwargs): return True
        def shutdown(self): pass
        def account_info(self): return NS(trade_mode=1, currency='USD', margin_mode=2, trade_allowed=True, trade_expert=True, equity=10000)
        def terminal_info(self): return NS(connected=True, trade_allowed=True, tradeapi_disabled=False)
        def positions_get(self): return [NS(ticket=n+1, sl=o['sl'], type=o['type'], symbol=o['symbol'], volume=o['volume'], price_open=o['price']) for n,o in enumerate(orders)]
        def symbol_info(self, symbol): return info
        def symbol_info_tick(self, symbol): return NS(ask=100, bid=99.8)
        def copy_rates_from_pos(self, symbol, tf, start, count):
            assert start == 1
            timeframe_calls.append(tf)
            return [dict(open=99, high=101, low=95, close=100, tick_volume=10, time=900)] * 200
        def order_calc_profit(self, side, symbol, volume, entry, stop): return -abs(entry-stop)*100*volume
        def order_check(self, request): return NS(retcode=0)
        def last_error(self): return 'none'
        def order_send(self, request):
            assert clock[0] < 1060
            orders.append(request)
            return NS(retcode=12, order=len(orders), price=request['price'], volume=request['volume'])
    class Client:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def get(self, path): return NS(raise_for_status=lambda:None, json=lambda:{'active':False})
    monkeypatch.setattr(runner.httpx, 'Client', Client)
    monkeypatch.setattr(runner.time, 'time', lambda:clock[0])
    monkeypatch.setattr(runner.time, 'sleep', lambda seconds:clock.__setitem__(0, clock[0]+seconds))
    strategies=[]
    def evaluate(strategy, candles, **kwargs):
        assert kwargs["fresh_structure"] == (variant in ("pluto3", "pluto4") and strategy == "market_structure")
        strategies.append(strategy)
        return NS(confluence=NS(direction='BUY', confluences=['test']), stop_loss=95)
    monkeypatch.setattr(runner, 'evaluate_catalog_strategy', evaluate)
    monkeypatch.setattr(runner, 'evaluate_pluto4_strategy', lambda strategy, candles, **kwargs: NS(confluence=NS(direction='BUY', confluences=['test']), stop_loss=95))
    args=NS(end_at=datetime.fromtimestamp(1060, timezone.utc).isoformat(), output_dir=str(tmp_path),
            variant=variant, symbol='GOLD', risk_dollars=0, total_risk_dollars=0, backend='http://test', interval=30, max_spread=.5)
    runner.run(args, Broker())
    assert len(orders) == (27 if disabled else 30)
    assert len({o['magic'] for o in orders}) == (27 if disabled else 30)
    if disabled:
        assert all(not 1302020060 <= o['magic'] <= 1302020062 for o in orders)
    assert set(strategies) == set(runner.CATALOG_STRATEGIES)
    assert set(timeframe_calls) == {15,30,60}
    assert len(list(tmp_path.glob('*-demo.jsonl'))) == 10
    assert len(runner.seen_signals(tmp_path/'sma_crossover-demo.jsonl')) == 3
    with pytest.raises(ValueError, match='cutoff_has_passed'):
        runner.run(args, Broker())
