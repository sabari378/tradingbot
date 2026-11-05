from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from nirv.core.enums import ExecutionMode, TradeDirection, TradeStatus


class TradeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(default="XAUUSD", min_length=1, max_length=32, pattern=r"^[A-Za-z0-9._#-]+$")
    direction: TradeDirection
    entry: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    take_profit: float = Field(gt=0)
    volume: float = Field(default=0.05, gt=0)
    risk_percent: float = Field(gt=0)
    confidence: float = Field(ge=0, le=1)
    mode: ExecutionMode = ExecutionMode.PAPER

    @model_validator(mode="after")
    def validate_prices(self) -> "TradeCreate":
        valid = (
            self.stop_loss < self.entry < self.take_profit
            if self.direction == TradeDirection.BUY
            else self.take_profit < self.entry < self.stop_loss
        )
        if not valid:
            raise ValueError("entry, stop loss, and take profit do not match trade direction")
        return self

    @property
    def calculated_risk_reward(self) -> float:
        return abs(self.take_profit - self.entry) / abs(self.entry - self.stop_loss)


class TradeCandidate(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    symbol: str = "XAUUSD"
    direction: TradeDirection
    entry: float
    stop_loss: float
    take_profit: float
    volume: float = 0.05
    risk_percent: float
    risk_reward: float = Field(gt=0)
    confidence: float
    status: TradeStatus = TradeStatus.PENDING
    mode: ExecutionMode = ExecutionMode.PAPER
    requested_at: datetime | None = None
    approved_at: datetime | None = None
    executed_at: datetime | None = None
    broker_ticket: str | None = None
    pnl: float | None = None
