from typing import Any

from nirv.agents.base import BaseAgent
from nirv.schemas.agent import AgentResult


class ChartAgent(BaseAgent):
    name, display_name = "chart", "Nirv Chart"

    async def analyze(self, context: dict[str, Any]) -> AgentResult:
        return AgentResult(
            agent=self.name,
            confidence=0.5,
            reasoning_summary="Chart analysis requires a configured market data provider.",
            signals=[],
            features={"market_data_connected": False, "trend": "unknown"},
        )


class LiquidityAgent(BaseAgent):
    name, display_name = "liquidity", "Nirv Liquidity"

    async def analyze(self, context: dict[str, Any]) -> AgentResult:
        return AgentResult(
            agent=self.name,
            confidence=0.5,
            reasoning_summary="Liquidity analysis is awaiting market data.",
            features={"market_data_connected": False},
        )


class VolumeAgent(BaseAgent):
    name, display_name = "volume", "Nirv Volume"

    async def analyze(self, context: dict[str, Any]) -> AgentResult:
        return AgentResult(
            agent=self.name,
            confidence=0.5,
            reasoning_summary="Tick-volume analysis is awaiting market data.",
            features={"volume_type": "tick", "market_data_connected": False},
        )


class NewsAgent(BaseAgent):
    name, display_name = "news", "Nirv News"

    async def analyze(self, context: dict[str, Any]) -> AgentResult:
        return AgentResult(
            agent=self.name,
            confidence=0.5,
            reasoning_summary="No news provider is configured; trading is conservatively blocked.",
            signals=["news_provider_unavailable"],
            features={"risk_level": "UNKNOWN", "trade_blocked": True},
        )


class SignalAgent(BaseAgent):
    name, display_name = "signal", "Nirv Signal"

    async def analyze(self, context: dict[str, Any]) -> AgentResult:
        return AgentResult(
            agent=self.name,
            confidence=0,
            reasoning_summary="No deterministic confluence is available without market data.",
            signals=[],
            features={"direction": None, "score": 0},
        )


class RiskAgent(BaseAgent):
    name, display_name = "risk", "Nirv Risk"

    async def analyze(self, context: dict[str, Any]) -> AgentResult:
        return AgentResult(
            agent=self.name,
            confidence=1,
            reasoning_summary="Risk policy is available and must approve every executable candidate.",
            features={"approved": False},
        )


class ExecutionAgent(BaseAgent):
    name, display_name = "execution", "Nirv Execution"

    async def analyze(self, context: dict[str, Any]) -> AgentResult:
        return AgentResult(
            agent=self.name,
            confidence=1,
            reasoning_summary="Paper execution is ready; MT5 remains a separately authenticated gateway.",
            features={"mode": "PAPER"},
        )
