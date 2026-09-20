import subprocess
import sys
from pathlib import Path

from nirv.core.config import get_settings
from nirv.services.paper_status import DATA_DIR

PROJECT_DIR = Path(__file__).resolve().parents[3]
SESSION_SCRIPT = PROJECT_DIR / "backend" / "demo_session.py"
_demo_process: subprocess.Popen[bytes] | None = None


async def start_gold_demo_session() -> dict[str, str | bool]:
    global _demo_process
    if _demo_process is not None and _demo_process.poll() is None:
        return {"started": False, "message": "Demo trading is already running."}

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output = DATA_DIR / "gold-demo-m5.jsonl"
    _demo_process = subprocess.Popen(
        [
            sys.executable,
            str(SESSION_SCRIPT),
            "--symbol",
            "GOLD.i#",
            "--timeframe",
            "M5",
            "--duration",
            str(get_settings().demo_session_duration_seconds),
            "--interval",
            "60",
            "--volume",
            "0.05",
            "--output",
            str(output),
        ],
        cwd=PROJECT_DIR,
        start_new_session=True,
    )
    hours = get_settings().demo_session_duration_seconds / 3600
    return {"started": True, "message": f"Started {hours:g}-hour DEMO trading for GOLD.i# on M5 at 0.05 volume."}
