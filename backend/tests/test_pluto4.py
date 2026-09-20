import pytest
from nirv.market.candles import Candle
from nirv.strategies import catalog as c


@pytest.mark.parametrize("direction,bar,accepted", [
    ("BUY", Candle(4,10,0,8), True), ("BUY", Candle(9,10,0,8), False),
    ("BUY", Candle(4,10,0,6), False), ("SELL", Candle(6,10,0,2), True),
    ("SELL", Candle(1,10,0,2), False), ("SELL", Candle(6,10,0,4), False),
    ("BUY", Candle(5,5,5,5), False)])
def test_sweep_confirmation_preserves_risk(monkeypatch, direction, bar, accepted):
    baseline=c._decision(direction, 5, 1 if direction == "BUY" else 9, 2, ["sweep"], True)
    monkeypatch.setattr(c, "evaluate_catalog_strategy", lambda *a, **kw: baseline)
    result=c.evaluate_pluto4_strategy("liquidity_sweep", [Candle(5,9,1,5)]*25+[bar], risk_reward=2)
    assert result.confluence.direction == (direction if accepted else None)
    if accepted:
        assert (result.entry,result.stop_loss,result.take_profit,result.volume_confirmed) == (baseline.entry,baseline.stop_loss,baseline.take_profit,True)
    else:
        assert result.confluence.confluences[0].startswith("filtered:")


@pytest.mark.parametrize("direction,extreme", [("BUY",True),("BUY",False),("SELL",True),("SELL",False)])
def test_engulf_requires_range_extreme(monkeypatch,direction,extreme):
    baseline=c._decision(direction,5,1,2,["engulf"],False)
    monkeypatch.setattr(c,"evaluate_catalog_strategy",lambda *a,**kw:baseline)
    candles=[Candle(5,10,0,5)]*25+[Candle(5,8,2,4)]
    candles += [Candle(4,11 if extreme and direction=="SELL" else 8,-1 if extreme and direction=="BUY" else 2,6)]
    result=c.evaluate_pluto4_strategy("engulfing_reversal",candles,risk_reward=2)
    assert result.confluence.direction == (direction if extreme else None)


@pytest.mark.parametrize("name", [n for n in c.CATALOG_STRATEGIES if n not in ("liquidity_sweep","engulfing_reversal")])
def test_other_eight_match_pluto3(name):
    candles=[Candle(i,i+2,i-2,i+1) for i in range(60)]
    assert c.evaluate_pluto4_strategy(name,candles,risk_reward=2) == c.evaluate_catalog_strategy(name,candles,risk_reward=2,fresh_structure=name=="market_structure")
