from fastapi import APIRouter

router = APIRouter(tags=["market"])


@router.get("/market/status")
async def market_status() -> dict[str, bool | str]:
    return {"connected": False, "message": "MARKET DATA NOT CONNECTED"}
