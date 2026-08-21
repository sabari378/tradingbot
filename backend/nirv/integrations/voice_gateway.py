import re
from enum import StrEnum


class VoiceIntent(StrEnum):
    ANALYZE = "ANALYZE"
    STATUS = "STATUS"
    POSITIONS = "POSITIONS"
    ACCOUNT = "ACCOUNT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    CLOSE = "CLOSE"
    HELP = "HELP"


def parse_voice_intent(text: str) -> tuple[VoiceIntent, str | None]:
    normalized = text.lower().strip()
    if "analyze" in normalized or "bias" in normalized:
        return VoiceIntent.ANALYZE, None
    if "position" in normalized:
        return VoiceIntent.POSITIONS, None
    if "account" in normalized or "risk" in normalized:
        return VoiceIntent.ACCOUNT, None
    if "approve" in normalized:
        return VoiceIntent.APPROVE, _trade_id(normalized)
    if "reject" in normalized:
        return VoiceIntent.REJECT, _trade_id(normalized)
    if "close" in normalized:
        return VoiceIntent.CLOSE, _trade_id(normalized)
    if "status" in normalized:
        return VoiceIntent.STATUS, None
    return VoiceIntent.HELP, None


def _trade_id(text: str) -> str | None:
    match = re.search(r"[0-9a-f]{8}-[0-9a-f-]{27,}", text)
    return match.group(0) if match else None
