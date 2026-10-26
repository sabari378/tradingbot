from urllib.parse import quote, unquote

import httpx
from fastapi import APIRouter, HTTPException, Query

from nirv.core.config import get_settings
from nirv.strategies.chart_patterns import analyze_price_action

router = APIRouter(tags=["market"])


@router.get("/market/status")
async def market_status() -> dict[str, bool | str]:
    return {"connected": False, "message": "MARKET DATA NOT CONNECTED"}


@router.get("/market/chart")
async def market_chart(
    symbol: str = "GOLD.i%23",
    timeframe: str = "M15",
    limit: int = Query(default=5000, ge=50, le=5000),
) -> dict:
    symbol = unquote(symbol)
    if timeframe not in {"M5", "M15", "H1"}:
        raise HTTPException(status_code=422, detail="unsupported timeframe")
    try:
        async with httpx.AsyncClient(base_url=get_settings().mt5_gateway_url, timeout=30) as client:
            response = await client.get(
                f"/candles/{quote(symbol, safe='')}/{timeframe}",
                params={"limit": limit, "include_current": False},
            )
            response.raise_for_status()
    except httpx.HTTPError as error:
        raise HTTPException(status_code=503, detail=f"market chart unavailable: {error}") from error

    candles = response.json()
    if not candles:
        raise HTTPException(status_code=503, detail="XM MT5 returned no closed candles")
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "candles": candles,
        "annotations": analyze_price_action(candles),
    }
