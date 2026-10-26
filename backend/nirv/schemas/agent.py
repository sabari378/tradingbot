from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class AgentResult(BaseModel):
    agent: str
    status: str = "completed"
    confidence: float = Field(ge=0, le=1)
    reasoning_summary: str
    signals: list[str] = []
    features: dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
