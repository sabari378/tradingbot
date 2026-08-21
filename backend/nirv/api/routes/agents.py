from fastapi import APIRouter

router = APIRouter(tags=["agents"])


@router.get("/agents")
async def list_agents() -> list[dict[str, str]]:
    return [
        {"name": "master", "display_name": "Nirv Master", "status": "ONLINE"},
        {"name": "chart", "display_name": "Nirv Chart", "status": "ONLINE"},
        {"name": "liquidity", "display_name": "Nirv Liquidity", "status": "ONLINE"},
        {"name": "volume", "display_name": "Nirv Volume", "status": "ONLINE"},
        {"name": "news", "display_name": "Nirv News", "status": "ONLINE"},
        {"name": "signal", "display_name": "Nirv Signal", "status": "ONLINE"},
        {"name": "risk", "display_name": "Nirv Risk", "status": "ONLINE"},
        {"name": "execution", "display_name": "Nirv Execution", "status": "STANDBY"},
    ]
