from fastapi import APIRouter, Depends

from nirv.core.security import require_api_key
from nirv.execution.demo import DemoExecutionEngine

router = APIRouter(tags=["account"])


@router.get("/account", dependencies=[Depends(require_api_key)])
async def account() -> dict:
    try:
        return await DemoExecutionEngine().account()
    except ValueError as error:
        return {"connected": False, "mode": "DEMO", "message": str(error)}
