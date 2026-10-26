from abc import ABC, abstractmethod
from typing import Any

from nirv.schemas.agent import AgentResult


class BaseAgent(ABC):
    name: str
    display_name: str

    @abstractmethod
    async def analyze(self, context: dict[str, Any]) -> AgentResult:
        raise NotImplementedError

    def unavailable(self, reason: str) -> AgentResult:
        return AgentResult(agent=self.name, status="unavailable", confidence=0, reasoning_summary=reason)
