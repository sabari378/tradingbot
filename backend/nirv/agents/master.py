from typing import Any

from nirv.agents.specialists import ChartAgent, LiquidityAgent, NewsAgent, RiskAgent, SignalAgent, VolumeAgent
from nirv.schemas.agent import AgentResult


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
        for agent in (self.chart, self.liquidity, self.volume, self.news):
            results.append(await agent.analyze(context))
        signal = await self.signal.analyze({**context, "agent_results": results})
        risk = await self.risk.analyze({**context, "signal": signal})
        results.extend((signal, risk))
        return {
            "symbol": context.get("symbol", "XAUUSD"),
            "direction": None,
            "confidence": 0,
            "approved_by_risk": False,
            "requires_user_approval": True,
            "agents": [result.model_dump(mode="json") for result in results],
            "rejection_reasons": ["market_data_not_connected", "news_provider_unavailable"],
        }
