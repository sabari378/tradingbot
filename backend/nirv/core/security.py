from fastapi import Depends, Header, HTTPException, status

from nirv.core.config import get_settings
from nirv.core.emergency_stop import emergency_stop


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    configured = get_settings().api_key
    if configured and x_api_key != configured:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid API key")


async def require_running(_: None = Depends(require_api_key)) -> None:
    if emergency_stop.active:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="emergency stop is active")
