from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from nirv.models.base import Base


class Trade(Base):
    __tablename__ = "trades"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    symbol: Mapped[str] = mapped_column(String(20), default="XAUUSD")
    direction: Mapped[str] = mapped_column(String(4))
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    entry: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    take_profit: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)
    risk_percent: Mapped[float] = mapped_column(Float)
    risk_amount: Mapped[float] = mapped_column(Float, default=0)
    rr: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    mode: Mapped[str] = mapped_column(String(10), default="PAPER")
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pnl: Mapped[float | None] = mapped_column(Float)
    broker_ticket: Mapped[str | None] = mapped_column(String(100))
