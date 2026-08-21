from fastapi import APIRouter, Depends

from nirv.core.security import require_api_key

router = APIRouter(tags=["account"])


@router.get("/account", dependencies=[Depends(require_api_key)])
async def account() -> dict[str, str | bool]:
    return {"connected": False, "mode": "PAPER", "message": "ACCOUNT NOT CONNECTED"}
