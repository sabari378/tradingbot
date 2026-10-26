import sqlite3
from pathlib import Path
from threading import Lock

from .models import CloseRequest, ModifyPositionRequest, OrderRequest
from .mt5_client import MT5Client


class Executor:
    def __init__(self, idempotency_db: Path | None = None) -> None:
        self.client = MT5Client()
        self.idempotency_db = idempotency_db or Path("mt5-idempotency.db")
        self._lock = Lock()
        with self._connect() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS orders (trade_id TEXT PRIMARY KEY, status TEXT NOT NULL)")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.idempotency_db, timeout=10)

    def execute(self, order: OrderRequest) -> dict:
        if order.mode != "DEMO":
            return {"success": False, "error": "only DEMO mode is accepted"}
        with self._lock, self._connect() as connection:
            try:
                connection.execute("INSERT INTO orders (trade_id, status) VALUES (?, 'PENDING')", (order.trade_id,))
            except sqlite3.IntegrityError:
                return {"success": False, "error": "duplicate trade_id"}
        result = self.client.order(order.model_dump())
        with self._lock, self._connect() as connection:
            if result.get("success"):
                connection.execute("UPDATE orders SET status = 'COMPLETED' WHERE trade_id = ?", (order.trade_id,))
            else:
                connection.execute("DELETE FROM orders WHERE trade_id = ?", (order.trade_id,))
        return result

    def close(self, request: CloseRequest) -> dict:
        if request.mode != "DEMO":
            return {"success": False, "error": "only DEMO mode is accepted"}
        return self.client.close_position(request.model_dump())

    def modify(self, request: ModifyPositionRequest) -> dict:
        if request.mode != "DEMO":
            return {"success": False, "error": "only DEMO mode is accepted"}
        return self.client.modify_position(request.model_dump())
