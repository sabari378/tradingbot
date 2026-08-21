from fastapi import APIRouter
from pydantic import BaseModel

from nirv.integrations.voice_gateway import parse_voice_intent

router = APIRouter(tags=["voice"])


class VoiceCommand(BaseModel):
    text: str
    confirmed: bool = False


@router.post("/voice/command")
async def voice_command(command: VoiceCommand) -> dict:
    intent, trade_id = parse_voice_intent(command.text)
    requires_confirmation = intent.value in {"APPROVE", "REJECT", "CLOSE"}
    if requires_confirmation and not command.confirmed:
        return {"intent": intent, "trade_id": trade_id, "requires_confirmation": True}
    return {"intent": intent, "trade_id": trade_id, "requires_confirmation": False}
