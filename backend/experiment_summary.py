import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize PAPER experiment JSONL files into a ranked CSV.")
    parser.add_argument("--experiment-dir", default="backend/data/experiments")
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=15)
    return parser.parse_args()


def read_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def max_drawdown(values: list[float]) -> float:
    peak = 0.0
    equity = 0.0
    drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return round(drawdown, 2)


def summarize(row: dict[str, str], path: Path) -> dict[str, str | int | float]:
    events = read_events(path)
    closed = [event for event in events if event.get("event") == "PAPER_CLOSED"]
    pnl = [float(event.get("pnl_points", 0)) for event in closed]
    gross_profit = sum(value for value in pnl if value > 0)
    gross_loss = abs(sum(value for value in pnl if value < 0))
    wins = sum(value > 0 for value in pnl)
    losses = sum(value < 0 for value in pnl)
    return {
        "strategy_id": row["strategy_id"],
        "timeframe": row["timeframe"],
        "signals": row["signals"],
        "require_volume": row["require_volume"],
        "risk_reward": float(row["risk_reward"]),
        "scans": sum(event.get("event") == "SCAN" for event in events),
        "trades": len(closed),
        "wins": wins,
        "losses": losses,
        "win_rate": round(wins / len(closed), 4) if closed else 0,
        "net_pnl_points": round(sum(pnl), 2),
        "average_pnl_points": round(sum(pnl) / len(closed), 2) if closed else 0,
        "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss else (999 if gross_profit else 0),
        "max_drawdown_points": max_drawdown(pnl),
        "completed": any(event.get("event") == "SESSION_FINISHED" for event in events),
    }


def main() -> None:
    args = parse_args()
    experiment_dir = Path(args.experiment_dir)
    manifest_path = experiment_dir / "manifest.csv"
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        manifest = list(csv.DictReader(handle))

    while args.wait:
        complete = sum(
            any(event.get("event") == "SESSION_FINISHED" for event in read_events(Path(row["output"])))
            for row in manifest
        )
        if complete == len(manifest):
            break
        time.sleep(args.poll_seconds)

    results = [summarize(row, Path(row["output"])) for row in manifest]
    results.sort(key=lambda row: (float(row["net_pnl_points"]), float(row["profit_factor"])), reverse=True)
    output = experiment_dir / "results.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print(f"Wrote {len(results)} experiment results to {output}")


if __name__ == "__main__":
    main()
