from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from nirv.core.config import get_settings
from nirv.core.emergency_stop import emergency_stop
from nirv.integrations.voice_gateway import parse_voice_intent
from nirv.services.demo_controller import start_gold_demo_session
from nirv.services.paper_controller import start_gold_paper_session
from nirv.services.paper_status import format_paper_status, get_paper_status
from nirv.services.trading_service import trading_service

router = APIRouter(tags=["voice"])


class VoiceCommand(BaseModel):
    text: str
    target: str = "nirv"
    confirmed: bool = False


BOT_CAPABILITIES = {
    "nirv": (
        "I am Nirv, the coordinator. Orion reads charts, Ripple tracks liquidity, Pulse measures volume, "
        "Beacon watches news, Atlas builds signals, Sentinel controls risk, and Forge handles approved execution."
    ),
    "chart": "I am Orion. I read candles, trends, breaks of structure, and market-structure shifts.",
    "liquidity": "I am Ripple. I locate liquidity pools, equal highs and lows, stop clusters, and sweeps.",
    "volume": "I am Pulse. I compare tick volume with its baseline to confirm whether a move has participation.",
    "news": "I am Beacon. I watch economic news and block trading when event risk is unsafe.",
    "signal": "I am Atlas. I combine structure, liquidity, imbalance, and volume into a potential trade setup.",
    "risk": "I am Sentinel. I enforce risk, spread, reward-to-risk, exposure, data-age, and loss limits.",
    "execution": "I am Forge. I send only approved paper or authenticated MT5 demo orders.",
}


@router.post("/voice/command")
async def voice_command(command: VoiceCommand, x_api_key: str | None = Header(default=None)) -> dict:
    target = command.target.lower()
    if target not in BOT_CAPABILITIES:
        raise HTTPException(status_code=422, detail="unknown bot target")
    normalized_text = command.text.lower()
    if "what can you do" in normalized_text or "what do you do" in normalized_text:
        return {
            "intent": "CAPABILITIES",
            "target": target,
            "trade_id": None,
            "requires_confirmation": False,
            "response": BOT_CAPABILITIES[target],
        }
    intent, trade_id = parse_voice_intent(command.text)
    if intent.value in {"START_PAPER", "START_DEMO"}:
        settings = get_settings()
        if not settings.api_key or x_api_key != settings.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="starting a trading session requires operator authentication",
            )
    if intent.value == "START_PAPER":
        result = start_gold_paper_session()
        return {
            "intent": intent,
            "trade_id": None,
            "requires_confirmation": False,
            "response": result["message"],
            **result,
        }
    if intent.value == "START_DEMO":
        if not get_settings().demo_trading_enabled:
            return {
                "intent": intent,
                "trade_id": None,
                "requires_confirmation": False,
                "started": False,
                "blocked": True,
                "response": "Demo trading is disabled. Enable it explicitly in backend settings.",
            }
        result = await start_gold_demo_session()
        return {
            "intent": intent,
            "trade_id": None,
            "requires_confirmation": False,
            "response": result["message"],
            **result,
        }
    requires_confirmation = intent.value in {"APPROVE", "REJECT", "CLOSE"}
    if requires_confirmation:
        settings = get_settings()
        if not settings.voice_trading_enabled:
            return {
                "intent": intent,
                "trade_id": trade_id,
                "requires_confirmation": False,
                "blocked": True,
                "response": "Voice trading is disabled. Enable it explicitly in backend settings.",
            }
        if not settings.api_key or x_api_key != settings.api_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="voice trade authentication required")
        if emergency_stop.active:
            return {
                "intent": intent,
                "trade_id": trade_id,
                "requires_confirmation": False,
                "blocked": True,
                "response": "Voice trading is blocked by the emergency stop.",
            }
    if requires_confirmation and not command.confirmed:
        return {
            "intent": intent,
            "trade_id": trade_id,
            "requires_confirmation": True,
            "response": f"{intent.value} requires your confirmation.",
        }
    if intent.value in {"APPROVE", "REJECT"}:
        if trade_id is None:
            raise HTTPException(status_code=422, detail="a trade ID is required")
        try:
            trade_uuid = UUID(trade_id)
            trade = (
                trading_service.approve(trade_uuid)
                if intent.value == "APPROVE"
                else trading_service.reject(trade_uuid)
            )
        except (KeyError, ValueError) as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {
            "intent": intent,
            "trade_id": trade_id,
            "requires_confirmation": False,
            "response": f"Trade {trade_id} is now {trade.status.value.lower()}.",
        }
    if intent.value == "CLOSE":
        return {
            "intent": intent,
            "trade_id": trade_id,
            "requires_confirmation": False,
            "blocked": True,
            "response": "Voice position closing is not implemented and no close request was sent.",
        }
    responses = {
        "ANALYZE": "Nirv is ready to analyze the selected market.",
        "STATUS": format_paper_status(get_paper_status()),
        "POSITIONS": "Position status is available from the execution gateway.",
        "ACCOUNT": "Account and risk status are available from the demo gateway.",
        "HELP": "Try: start PT, status, analyze GOLD, show positions, or account risk.",
    }
    return {"intent": intent, "trade_id": trade_id, "requires_confirmation": False, "response": responses[intent.value]}
