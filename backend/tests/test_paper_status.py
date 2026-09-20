import json

from nirv.services.paper_status import format_paper_status, get_paper_status


def test_paper_status_reports_inactive_session(tmp_path) -> None:
    log = tmp_path / "gold-paper-m5.jsonl"
    log.write_text(
        "\n".join(
            [
                json.dumps(
                    {"event": "SESSION_STARTED", "started_at": "2026-08-24T16:24:02+00:00", "symbol": "GOLD.i#"}
                ),
                json.dumps(
                    {
                        "event": "SCAN",
                        "timestamp": "2026-08-24T16:24:02+00:00",
                        "symbol": "GOLD.i#",
                        "direction": "BUY",
                        "score": 3,
                        "position_open": True,
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )
    status = get_paper_status(tmp_path)

    assert status["mode"] == "PAPER"
    assert status["active_sessions"] == 0
    assert status["sessions"][0]["direction"] == "BUY"
    assert "not currently running" in format_paper_status(status)