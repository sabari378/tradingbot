from nirv_mt5.executor import Executor
from nirv_mt5.models import CloseRequest, ModifyPositionRequest, OrderRequest


def order() -> OrderRequest:
    return OrderRequest(
        trade_id="trade-1",
        symbol="XAUUSD",
        side="BUY",
        volume=0.01,
        stop_loss=1990,
        take_profit=2020,
    )


def test_successful_order_remains_idempotent_after_restart(tmp_path) -> None:
    database = tmp_path / "orders.db"
    first = Executor(database)
    first.client.order = lambda payload: {"success": True, "ticket": "1"}
    assert first.execute(order())["success"] is True

    restarted = Executor(database)
    restarted.client.order = lambda payload: {"success": True, "ticket": "2"}
    assert restarted.execute(order()) == {"success": False, "error": "duplicate trade_id"}


def test_failed_order_can_be_retried(tmp_path) -> None:
    executor = Executor(tmp_path / "orders.db")
    executor.client.order = lambda payload: {"success": False, "error": "temporary failure"}
    assert executor.execute(order())["success"] is False

    executor.client.order = lambda payload: {"success": True, "ticket": "1"}
    assert executor.execute(order())["success"] is True


def test_position_management_rejects_non_demo_mode(tmp_path) -> None:
    executor = Executor(tmp_path / "orders.db")
    close = CloseRequest(ticket="1", symbol="XAUUSD", volume=0.01, mode="LIVE")
    modify = ModifyPositionRequest(ticket="1", symbol="XAUUSD", stop_loss=1990, take_profit=2020, mode="LIVE")
    assert executor.close(close)["success"] is False
    assert executor.modify(modify)["success"] is False
