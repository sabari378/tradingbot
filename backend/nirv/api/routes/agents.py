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
            "display_name": "Orion",
            "status": "ONLINE",
            "activity": "Reading market structure and candles",
            "color": "cyan",
        },
        {
            "name": "liquidity",
            "display_name": "Ripple",
            "status": "ONLINE",
            "activity": "Watching equal highs, lows, and sweeps",
            "color": "amber",
        },
        {
            "name": "volume",
            "display_name": "Pulse",
            "status": "ONLINE",
            "activity": "Comparing tick volume to its baseline",
            "color": "violet",
        },
        {
            "name": "news",
            "display_name": "Beacon",
            "status": "STANDBY",
            "activity": "No provider connected; trading remains guarded",
            "color": "red",
        },
        {
            "name": "signal",
            "display_name": "Atlas",
            "status": "ONLINE",
            "activity": "Waiting for complete ICT/SMC confluence",
            "color": "blue",
        },
        {
            "name": "risk",
            "display_name": "Sentinel",
            "status": "ONLINE",
            "activity": "Enforcing spread, R:R, and exposure limits",
            "color": "green",
        },
        {
            "name": "backtest",
            "display_name": "Chronos",
            "status": "ONLINE",
            "activity": "Replaying XM history without future data",
            "color": "teal",
        },
        {
            "name": "execution",
            "display_name": "Forge",
            "status": "STANDBY",
            "activity": "Armed only after explicit confirmation",
            "color": "orange",
        },
    ]
