from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from nirv.core.enums import ExecutionMode, TradeDirection, TradeStatus


class TradeCandidate(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    symbol: str = "XAUUSD"
    direction: TradeDirection
    entry: float
    stop_loss: float
    take_profit: float
    volume: float = 0.01
    risk_percent: float
    risk_reward: float
    confidence: float
    status: TradeStatus = TradeStatus.PENDING
    mode: ExecutionMode = ExecutionMode.PAPER
    requested_at: datetime | None = None
    approved_at: datetime | None = None
    executed_at: datetime | None = None
    broker_ticket: str | None = None
    pnl: float | None = None
