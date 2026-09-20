import argparse
import csv
import itertools
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SIGNALS = ("liquidity", "mss", "fvg")
TIMEFRAMES = ("M5", "M15", "H1")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch isolated concurrent PAPER strategy experiments.")
    parser.add_argument("--duration", type=int, default=7200)
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--symbol", default="GOLD.i#")
    parser.add_argument("--gateway", default="http://127.0.0.1:8100")
    parser.add_argument("--output-dir", default="backend/data/experiments")
    return parser.parse_args()


def combinations() -> list[tuple[str, ...]]:
    return [combo for size in range(1, len(SIGNALS) + 1) for combo in itertools.combinations(SIGNALS, size)]


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc)
    rows: list[dict[str, str | int | bool]] = []
    processes: list[subprocess.Popen[bytes]] = []

    for timeframe in TIMEFRAMES:
        for combo in combinations():
            for require_volume in (False, True):
                signal_name = "-".join(combo)
                strategy_id = f"{timeframe.lower()}-{signal_name}-vol-{int(require_volume)}"
                output = output_dir / f"{strategy_id}.jsonl"
                command = [
                    sys.executable,
                    "backend/paper_session.py",
                    "--symbol",
                    args.symbol,
                    "--timeframe",
                    timeframe,
                    "--duration",
                    str(args.duration),
                    "--interval",
                    str(args.interval),
                    "--gateway",
                    args.gateway,
                    "--strategy-id",
                    strategy_id,
                    "--signals",
                    ",".join(combo),
                    "--risk-reward",
                    "2.0",
                    "--allow-no-news",
                    "--output",
                    str(output),
                ]
                if require_volume:
                    command.append("--require-volume")
                process = subprocess.Popen(command, start_new_session=True)
                processes.append(process)
                rows.append(
                    {
                        "strategy_id": strategy_id,
                        "timeframe": timeframe,
                        "signals": "+".join(combo),
                        "require_volume": require_volume,
                        "risk_reward": 2.0,
                        "duration_seconds": args.duration,
                        "started_at": started.isoformat(),
                        "scheduled_end": (started + timedelta(seconds=args.duration)).isoformat(),
                        "pid": process.pid,
                        "output": str(output),
                    }
                )

    manifest = output_dir / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Started {len(processes)} concurrent PAPER experiments; manifest={manifest}")


if __name__ == "__main__":
    main()
