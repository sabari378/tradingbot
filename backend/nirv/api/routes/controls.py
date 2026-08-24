from fastapi import APIRouter, Depends
from pydantic import BaseModel

from nirv.core.emergency_stop import emergency_stop
from nirv.core.security import require_api_key

router = APIRouter(tags=["controls"])


class StopRequest(BaseModel):
    reason: str = "manual emergency stop"


@router.get("/controls/emergency-stop")
async def emergency_stop_status() -> dict:
    return emergency_stop.status()


@router.post("/controls/emergency-stop", dependencies=[Depends(require_api_key)])
async def engage_emergency_stop(request: StopRequest) -> dict:
    emergency_stop.engage(request.reason)
    return emergency_stop.status()


@router.delete("/controls/emergency-stop", dependencies=[Depends(require_api_key)])
async def reset_emergency_stop() -> dict:
    emergency_stop.reset()
    return emergency_stop.status()