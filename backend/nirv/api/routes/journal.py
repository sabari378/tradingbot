import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(tags=["journal"])

HISTORY_FILE = Path(__file__).resolve().parents[3] / "data" / "btcusd-paper-1h.jsonl"


@router.get("/audit")
async def audit() -> list[dict]:
    return []


@router.get("/paper-history")
async def paper_history(limit: int = 500) -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    records = [json.loads(line) for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines() if line]
    return records[-max(1, min(limit, 2000)) :]
