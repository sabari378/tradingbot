from datetime import datetime, timezone

from nirv.core.enums import ExecutionMode, TradeStatus
from nirv.schemas.trade import TradeCandidate


class PaperExecutionEngine:
    async def execute(self, trade: TradeCandidate) -> TradeCandidate:
        if trade.mode != ExecutionMode.PAPER:
            raise ValueError("paper engine only accepts PAPER mode")
        if trade.status != TradeStatus.APPROVED:
            raise ValueError("trade must be approved before execution")
        return trade.model_copy(update={"status": TradeStatus.FILLED, "executed_at": datetime.now(timezone.utc)})
