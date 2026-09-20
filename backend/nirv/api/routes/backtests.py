from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException

from nirv.agents.backtest import BacktestAgent
from nirv.core.config import get_settings
from nirv.core.security import require_api_key
from nirv.schemas.backtest import BacktestRequest, BacktestResponse

router = APIRouter(tags=["backtests"])


@router.post("/backtests/run", response_model=BacktestResponse, dependencies=[Depends(require_api_key)])
async def run_backtest(request: BacktestRequest) -> BacktestResponse:
    settings = get_settings()
    symbol_path = quote(request.symbol, safe="")
    params = {
        "date_from": request.date_from.isoformat(),
        "date_to": request.date_to.isoformat(),
    }
    try:
        async with httpx.AsyncClient(base_url=settings.mt5_gateway_url, timeout=60) as client:
            candles_response = await client.get(
                f"/historical-candles/{symbol_path}/{request.timeframe}", params=params
            )
            symbol_response = await client.get(f"/symbol/{symbol_path}")
            candles_response.raise_for_status()
            symbol_response.raise_for_status()
    except httpx.HTTPError as error:
        raise HTTPException(status_code=503, detail=f"XM MT5 history unavailable: {error}") from error

    candles = candles_response.json()
    symbol = symbol_response.json()
    if not candles:
        raise HTTPException(status_code=422, detail="XM MT5 returned no candles for this range")
    if len(candles) > 100_000:
        raise HTTPException(status_code=422, detail="backtest exceeds the 100,000 candle limit")
    if not symbol.get("available"):
        raise HTTPException(status_code=422, detail=symbol.get("error", "symbol is unavailable"))

    point = float(symbol.get("trade_tick_size") or 10 ** -int(symbol.get("digits", 2)))
    return BacktestAgent().run(request, candles, point=point)
