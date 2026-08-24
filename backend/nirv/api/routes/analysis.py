from datetime import datetime, timezone
from urllib.parse import quote, unquote

import httpx
from fastapi import APIRouter, HTTPException

from nirv.agents.master import NirvMasterAgent
from nirv.schemas.analysis import AnalysisRequest, AnalysisResponse

router = APIRouter(tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest) -> AnalysisResponse:
    result = await NirvMasterAgent().analyze(request.model_dump())
    return AnalysisResponse(**result)


@router.get("/analysis/live", response_model=AnalysisResponse)
async def live_analysis(symbol: str = "BTCUSD%23", timeframe: str = "M5") -> AnalysisResponse:
    symbol = unquote(symbol)
    from nirv.core.config import get_settings

    try:
        async with httpx.AsyncClient(base_url=get_settings().mt5_gateway_url, timeout=15) as client:
            candles_response = await client.get(f"/candles/{quote(symbol, safe='')}/{timeframe}", params={"limit": 200})
            quote_response = await client.get(f"/symbol/{quote(symbol, safe='')}")
            candles_response.raise_for_status()
            quote_response.raise_for_status()
    except httpx.HTTPError as error:
        raise HTTPException(status_code=503, detail=f"market data unavailable: {error}") from error

    candles = candles_response.json()
    quote_data = quote_response.json()
    result = await NirvMasterAgent().analyze(
        {"symbol": symbol, "candles": candles, "news_blocked": True}
    )
    result.update(
        {
            "market_data_connected": bool(candles) and quote_data.get("available", False),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "snapshot": {
                "timeframe": timeframe,
                "candle_count": len(candles),
                "bid": quote_data.get("bid"),
                "ask": quote_data.get("ask"),
                "latest_close": candles[-1].get("close") if candles else None,
                "latest_volume": candles[-1].get("volume") if candles else None,
            },
        }
    )
    return AnalysisResponse(**result)
