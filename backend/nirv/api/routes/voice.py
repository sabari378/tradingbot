from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from nirv.core.config import get_settings
from nirv.core.emergency_stop import emergency_stop
from nirv.integrations.voice_gateway import parse_voice_intent

router = APIRouter(tags=["voice"])


class VoiceCommand(BaseModel):
    text: str
    confirmed: bool = False


@router.post("/voice/command")
async def voice_command(command: VoiceCommand, x_api_key: str | None = Header(default=None)) -> dict:
    intent, trade_id = parse_voice_intent(command.text)
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
    responses = {
        "ANALYZE": "Nirv is ready to analyze the selected market.",
        "STATUS": "All core agents are online. Risk is active and execution is guarded.",
        "POSITIONS": "Position status is available from the execution gateway.",
        "ACCOUNT": "Account and risk status are available from the demo gateway.",
        "APPROVE": "Approval accepted for the requested trade.",
        "REJECT": "The requested trade was rejected.",
        "CLOSE": "Close request accepted for the requested trade.",
        "HELP": "Try: status, analyze BTCUSD, show positions, or account risk.",
    }
    return {"intent": intent, "trade_id": trade_id, "requires_confirmation": False, "response": responses[intent.value]}
