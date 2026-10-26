import pytest

from nirv.core.enums import ExecutionMode, TradeDirection, TradeStatus
from nirv.execution.paper import PaperExecutionEngine
from nirv.schemas.trade import TradeCandidate


@pytest.mark.asyncio
async def test_paper_execution_requires_user_approval() -> None:
    trade = TradeCandidate(
        direction=TradeDirection.BUY,
        entry=100,
        stop_loss=99,
        take_profit=102,
        risk_percent=0.25,
        risk_reward=2,
        confidence=0.8,
        status=TradeStatus.PENDING,
    )
    with pytest.raises(ValueError, match="approved"):
        await PaperExecutionEngine().execute(trade)


@pytest.mark.asyncio
async def test_live_mode_is_not_accepted_by_paper_engine() -> None:
    trade = TradeCandidate(
        direction=TradeDirection.BUY,
        entry=100,
        stop_loss=99,
        take_profit=102,
        risk_percent=0.25,
        risk_reward=2,
        confidence=0.8,
        status=TradeStatus.APPROVED,
        mode=ExecutionMode.DEMO,
    )
    with pytest.raises(ValueError, match="PAPER"):
        await PaperExecutionEngine().execute(trade)
