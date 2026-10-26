from fastapi import APIRouter

from nirv.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "service": "nirv", "mode": settings.nirv_mode.value}
