from .models import OrderRequest
from .mt5_client import MT5Client


class Executor:
    def __init__(self) -> None:
        self.client = MT5Client()

    def execute(self, order: OrderRequest) -> dict:
        if order.mode != "DEMO":
            return {"success": False, "error": "only DEMO mode is accepted"}
        return self.client.order(order.model_dump())
