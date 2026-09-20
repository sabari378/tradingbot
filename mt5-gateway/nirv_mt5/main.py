from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from starlette.concurrency import run_in_threadpool

from .config import GatewaySettings
from .executor import Executor
from .models import CloseRequest, ModifyPositionRequest, OrderRequest
from .security import gateway_auth

settings = GatewaySettings()
executor = Executor()
app = FastAPI(title="Nirv MT5 Demo Gateway")


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": "nirv-mt5-gateway",
        "mode": "DEMO",
        "bind": settings.host,
    }


@app.get("/account")
async def account(_: None = Depends(gateway_auth(settings))) -> dict:
    return executor.client.account()


@app.get("/positions")
async def positions(symbol: str | None = None, _: None = Depends(gateway_auth(settings))) -> list[dict]:
    return executor.client.positions(symbol)


@app.get("/history")
async def history() -> list:
    return []


@app.get("/symbol/{symbol}")
async def symbol(symbol: str) -> dict:
    return executor.client.symbol_details(symbol)


@app.get("/candles/{symbol}/{timeframe}")
async def candles(
    symbol: str, timeframe: str, limit: int = 200, include_current: bool = False
) -> list[dict]:
    try:
        return await run_in_threadpool(
            executor.client.candles, symbol, timeframe, limit, include_current
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/historical-candles/{symbol}/{timeframe}")
async def historical_candles(
    symbol: str,
    timeframe: str,
    date_from: Annotated[datetime, Query(description="Inclusive ISO-8601 timestamp with timezone")],
    date_to: Annotated[datetime, Query(description="Inclusive ISO-8601 timestamp with timezone")],
) -> list[dict]:
    try:
        return await run_in_threadpool(
            executor.client.historical_candles, symbol, timeframe, date_from, date_to
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/orders")
async def orders(
    order: OrderRequest, _: None = Depends(gateway_auth(settings))
) -> dict:
    return executor.execute(order)


@app.post("/orders/close")
async def close_order(
    order: CloseRequest, _: None = Depends(gateway_auth(settings))
) -> dict:
    return executor.close(order)


@app.post("/positions/modify")
async def modify_position(
    request: ModifyPositionRequest, _: None = Depends(gateway_auth(settings))
) -> dict:
    return executor.modify(request)
