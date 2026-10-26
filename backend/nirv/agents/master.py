from typing import Any

from nirv.agents.specialists import ChartAgent, LiquidityAgent, NewsAgent, RiskAgent, SignalAgent, VolumeAgent
from nirv.market.candles import Candle
from nirv.schemas.agent import AgentResult
from nirv.strategies.setup import analyze_setup


class NirvMasterAgent:
    name = "master"
    display_name = "Nirv Master"

    def __init__(self) -> None:
        self.chart = ChartAgent()
        self.liquidity = LiquidityAgent()
        self.volume = VolumeAgent()
        self.news = NewsAgent()
        self.signal = SignalAgent()
        self.risk = RiskAgent()

    async def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        results: list[AgentResult] = []
        raw_candles = context.get("candles", [])
        candles = [
            candle
            if isinstance(candle, Candle)
            else Candle(
                open=candle["open"],
                high=candle["high"],
                low=candle["low"],
                close=candle["close"],
                volume=candle.get("volume", 0),
            )
            for candle in raw_candles
        ]
        setup = analyze_setup(candles, news_blocked=context.get("news_blocked", True))
        agent_context = {**context, "candles": candles, "setup": setup}
        for agent in (self.chart, self.liquidity, self.volume, self.news):
            results.append(await agent.analyze(agent_context))
        signal = await self.signal.analyze({**agent_context, "agent_results": results})
        risk = await self.risk.analyze({**context, "signal": signal})
        results.extend((signal, risk))
        rejection_reasons = list(setup.confluence.confluences)
        if not setup.confluence.direction:
            rejection_reasons.extend(["no_confluence"] if candles else ["market_data_not_connected"])
        return {
            "symbol": context.get("symbol", "XAUUSD"),
            "direction": setup.confluence.direction,
            "confidence": setup.confluence.score / 4,
            "entry": setup.entry,
            "stop_loss": setup.stop_loss,
            "take_profit": setup.take_profit,
            "risk_reward": 2.0 if setup.entry is not None else None,
            "approved_by_risk": False,
            "requires_user_approval": True,
            "agents": [result.model_dump(mode="json") for result in results],
            "rejection_reasons": rejection_reasons
            + (["news_provider_unavailable"] if context.get("news_blocked", True) else []),
        }
