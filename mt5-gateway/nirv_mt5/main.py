from fastapi import Depends, FastAPI

from .config import GatewaySettings
from .executor import Executor
from .models import CloseRequest, OrderRequest
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
async def positions() -> list:
    return []


@app.get("/history")
async def history() -> list:
    return []


@app.get("/symbol/{symbol}")
async def symbol(symbol: str) -> dict:
    return executor.client.symbol_details(symbol)


@app.get("/candles/{symbol}/{timeframe}")
async def candles(symbol: str, timeframe: str, limit: int = 200) -> list[dict]:
    return executor.client.candles(symbol, timeframe, limit)


@app.post("/orders")
async def orders(
    order: OrderRequest, _: None = Depends(gateway_auth(settings))
) -> dict:
    return executor.execute(order)


@app.post("/orders/close")
async def close_order(
    order: CloseRequest, _: None = Depends(gateway_auth(settings))
) -> dict:
    return {
        "success": False,
        "error": "close requires configured MT5 terminal",
        "ticket": order.ticket,
    }
