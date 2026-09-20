import re
from enum import StrEnum


class VoiceIntent(StrEnum):
    START_PAPER = "START_PAPER"
    START_DEMO = "START_DEMO"
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
    if re.search(r"\b(start|run|begin)\s+(demo(?:\s+trading)?|demo account)\b", normalized):
        return VoiceIntent.START_DEMO, None
    if re.search(r"\b(start|run|begin)\s+(pt|paper(?:\s+trading)?|paper session)\b", normalized):
        return VoiceIntent.START_PAPER, None
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
