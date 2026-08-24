from .models import OrderRequest
from .mt5_client import MT5Client


class Executor:
    def __init__(self) -> None:
        self.client = MT5Client()
        self.completed_trade_ids: set[str] = set()

    def execute(self, order: OrderRequest) -> dict:
        if order.mode != "DEMO":
            return {"success": False, "error": "only DEMO mode is accepted"}
        if order.trade_id in self.completed_trade_ids:
            return {"success": False, "error": "duplicate trade_id"}
        result = self.client.order(order.model_dump())
        if result.get("success"):
            self.completed_trade_ids.add(order.trade_id)
        return result
