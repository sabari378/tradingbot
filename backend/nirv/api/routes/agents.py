from fastapi import APIRouter

router = APIRouter(tags=["agents"])


@router.get("/agents")
async def list_agents() -> list[dict[str, str]]:
    return [
        {
            "name": "master",
            "display_name": "Nirv Master",
            "status": "ONLINE",
            "activity": "Coordinating the decision chain",
            "color": "mint",
        },
        {
            "name": "chart",
            "display_name": "Nirv Chart",
            "status": "ONLINE",
            "activity": "Reading market structure and candles",
            "color": "cyan",
        },
        {
            "name": "liquidity",
            "display_name": "Nirv Liquidity",
            "status": "ONLINE",
            "activity": "Watching equal highs, lows, and sweeps",
            "color": "amber",
        },
        {
            "name": "volume",
            "display_name": "Nirv Volume",
            "status": "ONLINE",
            "activity": "Comparing tick volume to its baseline",
            "color": "violet",
        },
        {
            "name": "news",
            "display_name": "Nirv News",
            "status": "STANDBY",
            "activity": "No provider connected; trading remains guarded",
            "color": "red",
        },
        {
            "name": "signal",
            "display_name": "Nirv Signal",
            "status": "ONLINE",
            "activity": "Waiting for complete ICT/SMC confluence",
            "color": "blue",
        },
        {
            "name": "risk",
            "display_name": "Nirv Risk",
            "status": "ONLINE",
            "activity": "Enforcing spread, R:R, and exposure limits",
            "color": "green",
        },
        {
            "name": "execution",
            "display_name": "Nirv Execution",
            "status": "STANDBY",
            "activity": "Armed only after explicit confirmation",
            "color": "orange",
        },
    ]
