from datetime import datetime, timezone
from uuid import UUID

from nirv.core.config import get_settings
from nirv.core.enums import TradeStatus
from nirv.schemas.trade import TradeCandidate, TradeCreate


class TradingService:
    def __init__(self) -> None:
        self.trades: dict[UUID, TradeCandidate] = {}

    def create(self, request: TradeCreate) -> TradeCandidate:
        settings = get_settings()
        if request.risk_percent > settings.max_risk_percent:
            raise ValueError("risk percent exceeds configured maximum")
        if request.calculated_risk_reward < settings.min_risk_reward:
            raise ValueError("risk/reward is below configured minimum")
        trade = TradeCandidate(
            **request.model_dump(),
            risk_reward=request.calculated_risk_reward,
            requested_at=datetime.now(timezone.utc),
        )
        self.trades[trade.id] = trade
        return trade

    def get(self, trade_id: UUID) -> TradeCandidate | None:
        return self.trades.get(trade_id)

    def approve(self, trade_id: UUID) -> TradeCandidate:
        trade = self._required(trade_id)
        if trade.status != TradeStatus.PENDING:
            raise ValueError("only pending trades can be approved")
        updated = trade.model_copy(update={"status": TradeStatus.APPROVED, "approved_at": datetime.now(timezone.utc)})
        self.trades[trade_id] = updated
        return updated

    def reject(self, trade_id: UUID) -> TradeCandidate:
        trade = self._required(trade_id)
        updated = trade.model_copy(update={"status": TradeStatus.REJECTED})
        self.trades[trade_id] = updated
        return updated

    def _required(self, trade_id: UUID) -> TradeCandidate:
        trade = self.get(trade_id)
        if not trade:
            raise KeyError(str(trade_id))
        return trade


trading_service = TradingService()
