from fastapi import APIRouter

router = APIRouter(tags=["journal"])


@router.get("/audit")
async def audit() -> list[dict]:
    return []
