class MT5Client:
    def __init__(self) -> None:
        try:
            import MetaTrader5 as mt5
        except ImportError:
            mt5 = None
        self.mt5 = mt5

    def available(self) -> bool:
        return self.mt5 is not None

    def account(self) -> dict:
        return {"connected": self.available(), "mode": "DEMO"}

    def order(self, payload: dict) -> dict:
        if not self.available():
            return {"success": False, "error": "MetaTrader5 package is not installed"}
        return {
            "success": False,
            "error": "MT5 order implementation requires terminal configuration",
        }
