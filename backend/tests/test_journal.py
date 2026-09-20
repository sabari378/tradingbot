import pytest
from httpx import ASGITransport, AsyncClient

from nirv.api.main import app
from nirv.api.routes import journal


@pytest.mark.asyncio
async def test_paper_history_endpoint_returns_records() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/paper-history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_strategy_tests_groups_each_journal_as_a_run(monkeypatch, tmp_path) -> None:
    run = tmp_path / "venus-v2-test.jsonl"
    run.write_text(
        "\n".join(
            [
                '{"event":"VENUS_V2_STARTED","timestamp":"2026-01-01T00:00:00+00:00","duration_seconds":3600}',
                '{"event":"VENUS_V2_SCAN","timestamp":"2026-01-01T00:05:00+00:00"}',
                '{"event":"VENUS_V2_REJECTED","reason":"opposing_structure_too_close"}',
                '{"event":"VENUS_V2_FINISHED","timestamp":"2026-01-01T01:00:00+00:00"}',
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(journal, "DATA_DIR", tmp_path)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/strategy-tests")

    assert response.status_code == 200
    result = response.json()[0]
    assert result["strategy"] == "Venus v2"
    assert result["status"] == "completed"
    assert result["scans"] == 1
    assert result["rejections"] == 1
