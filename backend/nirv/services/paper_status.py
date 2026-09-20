import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _read_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def get_paper_status(data_dir: Path = DATA_DIR) -> dict[str, Any]:
    sessions: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)
    paths = sorted([*data_dir.glob("*-paper-*.jsonl"), *data_dir.glob("*-demo-*.jsonl")])
    for path in paths:
        events = _read_events(path)
        scans = [event for event in events if event.get("event") in {"SCAN", "DEMO_SCAN"}]
        if not events:
            continue
        latest = scans[-1] if scans else events[-1]
        latest_time = latest.get("timestamp") or events[0].get("started_at")
        age_seconds = None
        if latest_time:
            try:
                age_seconds = max(0, int((now - datetime.fromisoformat(latest_time)).total_seconds()))
            except ValueError:
                pass
        sessions.append(
            {
                "timeframe": path.stem.rsplit("-", 1)[-1].upper(),
                "symbol": events[0].get("symbol"),
                "active": latest.get("event") not in {"SESSION_FINISHED", "DEMO_SESSION_FINISHED"}
                and (age_seconds is None or age_seconds <= 120),
                "scan_count": len(scans),
                "last_scan_at": latest_time,
                "direction": latest.get("direction") or latest.get("price_action_vote"),
                "score": latest.get("score", 0),
                "position_open": latest.get("position_open", False),
                "bid": latest.get("bid"),
                "ask": latest.get("ask"),
            }
        )
    return {"mode": "PAPER", "active_sessions": sum(session["active"] for session in sessions), "sessions": sessions}


def format_paper_status(status: dict[str, Any]) -> str:
    sessions = status["sessions"]
    if not sessions:
        return "Paper trading is not currently running. No paper-session logs were found."
    active = [session for session in sessions if session["active"]]
    if not active:
        return "Paper trading is not currently running. The last recorded sessions are inactive."
    details = "; ".join(
        f"{session['symbol']} {session['timeframe']}: {session['direction'] or 'no signal'}, "
        f"score {session['score']}, {'position open' if session['position_open'] else 'no position'}"
        for session in active
    )
    return f"Paper trading is active in PAPER mode across {len(active)} timeframe session(s). {details}."