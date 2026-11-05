import subprocess
import sys
from pathlib import Path

from nirv.services.paper_status import DATA_DIR, get_paper_status


PROJECT_DIR = Path(__file__).resolve().parents[3]
SESSION_SCRIPT = PROJECT_DIR / "backend" / "paper_session.py"
TIMEFRAMES = ("M5", "M15", "H1")


def start_gold_paper_session() -> dict:
    status = get_paper_status()
    if status["active_sessions"]:
        return {"started": False, "message": "Paper trading is already running."}

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for timeframe in TIMEFRAMES:
        output = DATA_DIR / f"gold-paper-{timeframe.lower()}.jsonl"
        subprocess.Popen(
            [
                sys.executable,
                str(SESSION_SCRIPT),
                "--symbol",
                "GOLD.i#",
                "--timeframe",
                timeframe,
                "--duration",
                "3600",
                "--interval",
                "60",
                "--output",
                str(output),
            ],
            cwd=PROJECT_DIR,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
    return {"started": True, "message": "Started one-hour PAPER trading for GOLD.i# on M5, M15, and H1."}