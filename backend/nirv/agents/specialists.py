from typing import Any

from nirv.agents.base import BaseAgent
from nirv.schemas.agent import AgentResult


class ChartAgent(BaseAgent):
    name, display_name = "chart", "Orion"

    async def analyze(self, context: dict[str, Any]) -> AgentResult:
        candles = context.get("candles", [])
        latest = candles[-1] if candles else None
        trend = "bullish" if latest and latest.close > latest.open else "bearish" if latest else "unknown"
        return AgentResult(
            agent=self.name,
            confidence=0.7 if latest else 0.0,
            reasoning_summary=(
                f"Read {len(candles)} closed candles; latest candle is {trend}."
                if latest
                else "No candle data received."
            ),
            features={
                "market_data_connected": bool(candles),
                "trend": trend,
                "latest_close": latest.close if latest else None,
            },
        )


class LiquidityAgent(BaseAgent):
    name, display_name = "liquidity", "Ripple"

    async def analyze(self, context: dict[str, Any]) -> AgentResult:
        setup = context.get("setup")
        sweep_confirmed = bool(
            setup
            and setup.confluence.confluences
            and "news_blackout" not in setup.confluence.confluences
        )
        return AgentResult(
            agent=self.name,
            confidence=0.8 if sweep_confirmed else 0.4,
            reasoning_summary=(
                f"Liquidity sweep state: {setup.confluence.confluences[0]}."
                if sweep_confirmed
                else "No liquidity sweep confirmed in the current lookback."
            ),
            features={
                "market_data_connected": bool(context.get("candles")),
                "sweep_confirmed": sweep_confirmed,
            },
        )


class VolumeAgent(BaseAgent):
    name, display_name = "volume", "Pulse"

    async def analyze(self, context: dict[str, Any]) -> AgentResult:
        candles = context.get("candles", [])
        latest_volume = candles[-1].volume if candles else 0
        average_volume = sum(candle.volume for candle in candles[-21:-1]) / 20 if len(candles) >= 21 else 0
        confirmed = average_volume > 0 and latest_volume >= average_volume * 1.2
        return AgentResult(
            agent=self.name,
            confidence=1.0 if confirmed else 0.4,
            reasoning_summary=(
                f"Latest tick volume {latest_volume:.0f} vs {average_volume:.0f} baseline; "
                f"confirmation is {'present' if confirmed else 'absent'}."
                if candles
                else "No volume data received."
            ),
            features={
                "volume_type": "tick",
                "market_data_connected": bool(candles),
                "confirmed": confirmed,
            },
        )


class NewsAgent(BaseAgent):
    name, display_name = "news", "Beacon"

    async def analyze(self, context: dict[str, Any]) -> AgentResult:
        return AgentResult(
            agent=self.name,
            confidence=0.5,
            reasoning_summary="No news provider is configured; trading is conservatively blocked.",
            signals=["news_provider_unavailable"],
            features={"risk_level": "UNKNOWN", "trade_blocked": True},
        )


class SignalAgent(BaseAgent):
    name, display_name = "signal", "Atlas"

    async def analyze(self, context: dict[str, Any]) -> AgentResult:
        setup = context.get("setup")
        score = setup.confluence.score if setup else 0
        direction = setup.confluence.direction if setup else None
        return AgentResult(
            agent=self.name,
            confidence=score / 4,
            reasoning_summary=(
                f"Confluence score {score}/4; direction is {direction or 'none'}."
                if setup
                else "Signal engine did not receive a setup result."
            ),
            features={"direction": direction, "score": score},
        )


class RiskAgent(BaseAgent):
    name, display_name = "risk", "Sentinel"

    async def analyze(self, context: dict[str, Any]) -> AgentResult:
        return AgentResult(
            agent=self.name,
            confidence=1,
            reasoning_summary="Risk policy is available and must approve every executable candidate.",
            features={"approved": False},
        )


class ExecutionAgent(BaseAgent):
    name, display_name = "execution", "Forge"

    async def analyze(self, context: dict[str, Any]) -> AgentResult:
        return AgentResult(
            agent=self.name,
            confidence=1,
            reasoning_summary="Paper execution is ready; MT5 remains a separately authenticated gateway.",
            features={"mode": "PAPER"},
        )
