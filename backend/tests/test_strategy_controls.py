from pathlib import Path
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from nirv.api.main import app
from nirv.core.config import get_settings
from nirv.services import strategy_controls as controls


def test_controls_persist_and_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(controls, 'controls_path', lambda: tmp_path/'controls.json')
    assert controls.strategy_enabled('market_structure')
    controls.set_strategy_enabled('market_structure', False)
    assert not controls.strategy_enabled('market_structure')
    assert controls.strategy_enabled('liquidity_sweep')
    controls.set_strategy_enabled('liquidity_sweep', False)
    assert not controls.strategy_enabled('market_structure')
    with pytest.raises(ValueError): controls.set_strategy_enabled('unknown', True)
    (tmp_path/'controls.json').write_text('broken')
    assert not controls.strategy_enabled('market_structure')


@pytest.mark.asyncio
async def test_toggle_requires_authentication_and_valid_strategy(tmp_path, monkeypatch):
    monkeypatch.setattr(controls, 'controls_path', lambda: tmp_path/'controls.json')
    settings=get_settings()
    monkeypatch.setattr(settings, 'api_key', 'test-strategy-key')
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        r=await client.post('/api/v1/strategies/market_structure/enabled',json={'enabled':False})
        assert r.status_code==401
        headers={'X-API-Key':'test-strategy-key'}
        r=await client.post('/api/v1/strategies/market_structure/enabled',json={'enabled':False},headers=headers)
        assert r.status_code==200
        assert not controls.strategy_enabled('market_structure')
        r=await client.post('/api/v1/strategies/missing/enabled',json={'enabled':False},headers=headers)
        assert r.status_code==400
        r=await client.post('/api/v1/strategies/market_structure/enabled',json={'enabled':'false'},headers=headers)
        assert r.status_code==422
