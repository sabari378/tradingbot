import subprocess
import sys
from pathlib import Path
from threading import Lock

from nirv.core.config import get_settings
from nirv.services.paper_status import DATA_DIR, get_paper_status

PROJECT_DIR = Path(__file__).resolve().parents[3]
SESSION_SCRIPT = PROJECT_DIR / "backend" / "paper_session.py"
TIMEFRAMES = ("M5", "M15", "H1")
_start_lock = Lock()


def start_gold_paper_session() -> dict:
    with _start_lock:
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
                    str(get_settings().paper_session_duration_seconds),
                    "--interval",
                    "60",
                    "--allow-no-news",
                    "--output",
                    str(output),
                ],
                cwd=PROJECT_DIR,
                start_new_session=True,
            )
    return {"started": True, "message": "Started one-hour PAPER trading for GOLD.i# on M5, M15, and H1."}
