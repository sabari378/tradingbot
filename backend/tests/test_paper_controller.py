from nirv.services import paper_controller


def test_start_gold_paper_session_launches_three_timeframes(monkeypatch, tmp_path) -> None:
    launched = []
    monkeypatch.setattr(paper_controller, "DATA_DIR", tmp_path)
    monkeypatch.setattr(paper_controller, "get_paper_status", lambda: {"active_sessions": 0})
    monkeypatch.setattr(
        paper_controller.subprocess,
        "Popen",
        lambda command, **kwargs: launched.append((command, kwargs)),
    )

    result = paper_controller.start_gold_paper_session()

    assert result["started"] is True
    assert len(launched) == 3
    assert [command[command.index("--timeframe") + 1] for command, _ in launched] == ["M5", "M15", "H1"]
    assert all(command[command.index("--symbol") + 1] == "GOLD.i#" for command, _ in launched)
    assert all("--allow-no-news" in command for command, _ in launched)
