import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


def load_runner():
    spec = importlib.util.spec_from_file_location('venus_runner', Path(__file__).parents[1] / 'demo_venus_v2_session.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
@pytest.mark.parametrize('cap,expected', [(0, 3), (1, 0)])
async def test_concurrent_entries_preserve_existing_positions_and_deduplicate(tmp_path, monkeypatch, cap, expected):
    runner = load_runner()
    clock = [0]
    requests = []
    orders = []
    positions = [dict(ticket=str(n), magic=runner.MAGIC, price_open=100, stop_loss=95,
                      take_profit=110, side='BUY', price_current=100, volume=0.01) for n in (1, 2)]

    class Engine:
        async def account(self):
            return dict(connected=True, mode='DEMO', equity=10000)
        async def positions(self, symbol):
            return positions
        async def execute(self, trade):
            orders.append(trade)
            ticket = str(10 + len(orders))
            positions.append(dict(ticket=ticket, magic=runner.MAGIC, price_open=100, stop_loss=95,
                                  take_profit=110, side='BUY', price_current=100, volume=0.01))
            return SimpleNamespace(broker_ticket=ticket)

    class Response:
        def __init__(self, data): self.data = data
        def raise_for_status(self): pass
        def json(self): return self.data

    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def get(self, path, **kwargs):
            requests.append(path)
            if 'emergency-stop' in path: return Response({'active': False})
            if '/symbol/' in path:
                return Response(dict(ask=100, bid=99.9, trade_tick_size=.01, trade_tick_value=1,
                                     volume_min=.01, volume_step=.01, volume_max=50))
            return Response([dict(open=99, high=101, low=95, close=100, volume=100, time=123)])

    async def sleep(seconds): clock[0] += seconds
    monkeypatch.setattr(runner, 'DemoExecutionEngine', Engine)
    monkeypatch.setattr(runner.httpx, 'AsyncClient', Client)
    monkeypatch.setattr(runner.asyncio, 'get_running_loop', lambda: SimpleNamespace(time=lambda: clock[0]))
    monkeypatch.setattr(runner.asyncio, 'sleep', sleep)
    monkeypatch.setattr(runner, 'analyze_setup', lambda *a, **k: SimpleNamespace(
        stop_loss=95, confluence=SimpleNamespace(direction='BUY', score=2, confluences=['bullish_mss', 'bullish_fvg'])))
    monkeypatch.setattr(runner, 'target_before_opposing_structure', lambda *a, **k: (110, 2))
    args = SimpleNamespace(symbol='GOLD.i#', timeframes='M15,M30,H1', reversal_timeframe='M15',
                           max_positions=cap, duration=2, interval=1, risk_percent=.25, max_volume=.05,
                           desired_risk_reward=2, minimum_risk_reward=1.2, stop_buffer_atr=.1,
                           min_stop_distance=1, max_stop_distance=25, gateway='http://test',
                           backend='http://test', output=str(tmp_path / 'session.jsonl'))
    await runner.run_session(args)
    assert len(orders) == expected
    assert all('/M5' not in path for path in requests)
    assert {path.rsplit('/', 1)[-1] for path in requests if '/candles/' in path} == {'M15', 'M30', 'H1'}
    assert len(positions) == 2 + expected
