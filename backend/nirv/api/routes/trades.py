from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from nirv.core.enums import ExecutionMode
from nirv.core.security import require_api_key, require_running
from nirv.execution.demo import DemoExecutionEngine
from nirv.execution.paper import PaperExecutionEngine
from nirv.schemas.trade import TradeCandidate, TradeCreate
from nirv.services.trading_service import trading_service

router = APIRouter(tags=["trades"])


@router.post("/trades", dependencies=[Depends(require_api_key)])
async def create_trade(trade: TradeCreate) -> TradeCandidate:
    try:
        return trading_service.create(trade)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error


@router.get("/trades")
async def list_trades() -> list[TradeCandidate]:
    return list(trading_service.trades.values())


@router.get("/trades/{trade_id}")
async def get_trade(trade_id: UUID) -> TradeCandidate:
    trade = trading_service.get(trade_id)
    if not trade:
        raise HTTPException(404, "trade not found")
    return trade


@router.post("/trades/{trade_id}/approve", dependencies=[Depends(require_api_key)])
async def approve_trade(trade_id: UUID) -> TradeCandidate:
    try:
        return trading_service.approve(trade_id)
    except KeyError:
        raise HTTPException(404, "trade not found")
    except ValueError as error:
        raise HTTPException(409, str(error))


@router.post("/trades/{trade_id}/reject", dependencies=[Depends(require_api_key)])
async def reject_trade(trade_id: UUID) -> TradeCandidate:
    try:
        return trading_service.reject(trade_id)
    except KeyError:
        raise HTTPException(404, "trade not found")


@router.post("/trades/{trade_id}/execute", dependencies=[Depends(require_running)])
async def execute_trade(trade_id: UUID) -> TradeCandidate:
    trade = trading_service.get(trade_id)
    if not trade:
        raise HTTPException(404, "trade not found")
    try:
        engine = DemoExecutionEngine() if trade.mode == ExecutionMode.DEMO else PaperExecutionEngine()
        executed = await engine.execute(trade)
    except ValueError as error:
        raise HTTPException(409, str(error))
    trading_service.trades[trade_id] = executed
    return executed
