import json
from pathlib import Path

from fastapi import APIRouter

from nirv.services.paper_status import get_paper_status

router = APIRouter(tags=["journal"])

DATA_DIR = Path(__file__).resolve().parents[3] / "data"


@router.get("/audit")
async def audit() -> list[dict]:
    return []


@router.get("/paper-history")
async def paper_history(limit: int = 500) -> list[dict]:
    records: list[dict] = []
    history_files = sorted([*DATA_DIR.glob("*-paper-*.jsonl"), *DATA_DIR.glob("*-demo-*.jsonl")])
    for history_file in history_files:
        for line in history_file.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
    records.sort(key=lambda record: record.get("timestamp") or record.get("started_at") or "")
    return records[-max(1, min(limit, 2000)) :]


@router.get("/paper-status")
async def paper_status() -> dict:
    return get_paper_status()
