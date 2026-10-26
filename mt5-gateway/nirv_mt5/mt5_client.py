from datetime import datetime, timezone


class MT5Client:
    def __init__(self) -> None:
        try:
            import MetaTrader5 as mt5
        except ImportError:
            mt5 = None
        self.mt5 = mt5

    def available(self) -> bool:
        return self.mt5 is not None

    def _initialize(self) -> bool:
        return bool(self.mt5 and self.mt5.initialize(timeout=5000))

    @staticmethod
    def _serialize_rates(rates) -> list[dict]:
        if rates is None:
            return []
        return [
            {
                "time": int(rate["time"]),
                "open": float(rate["open"]),
                "high": float(rate["high"]),
                "low": float(rate["low"]),
                "close": float(rate["close"]),
                "volume": float(rate["tick_volume"]),
                "spread": int(rate["spread"]),
                "real_volume": float(rate["real_volume"]),
            }
            for rate in rates
        ]

    def account(self) -> dict:
        if not self.available() or not self.mt5.initialize():
            error = str(self.mt5.last_error()) if self.mt5 else "MetaTrader5 package is not installed"
            return {"connected": False, "mode": "DEMO", "error": error}
        account = self.mt5.account_info()
        self.mt5.shutdown()
        if account is None:
            return {"connected": False, "mode": "DEMO", "error": str(self.mt5.last_error())}
        return {
            "connected": True,
            "mode": "DEMO",
            "login": account.login,
            "server": account.server,
            "balance": float(account.balance),
            "equity": float(account.equity),
            "currency": account.currency,
        }

    def symbol_details(self, symbol: str) -> dict:
        if not self.available() or not self.mt5.initialize():
            error = str(self.mt5.last_error()) if self.mt5 else "MetaTrader5 package is not installed"
            return {"available": False, "error": error}

        try:
            info = self.mt5.symbol_info(symbol)
            tick = self.mt5.symbol_info_tick(symbol)
            if info is None or tick is None:
                return {"available": False, "symbol": symbol, "error": str(self.mt5.last_error())}
            return {
                "available": bool(info.visible),
                "symbol": symbol,
                "bid": tick.bid,
                "ask": tick.ask,
                "digits": info.digits,
                "volume_min": info.volume_min,
                "volume_step": info.volume_step,
                "volume_max": info.volume_max,
                "trade_tick_size": info.trade_tick_size,
                "trade_tick_value": info.trade_tick_value,
            }
        finally:
            self.mt5.shutdown()

    def candles(
        self, symbol: str, timeframe: str, limit: int = 200, include_current: bool = False
    ) -> list[dict]:
        if not self.available() or not self._initialize():
            return []

        timeframe_constant = getattr(self.mt5, f"TIMEFRAME_{timeframe.upper()}", None)
        if timeframe_constant is None:
            self.mt5.shutdown()
            raise ValueError(f"unsupported timeframe: {timeframe}")

        try:
            start_position = 0 if include_current else 1
            rates = self.mt5.copy_rates_from_pos(symbol, timeframe_constant, start_position, min(limit, 5000))
            return self._serialize_rates(rates)
        finally:
            self.mt5.shutdown()

    def historical_candles(
        self, symbol: str, timeframe: str, date_from: datetime, date_to: datetime
    ) -> list[dict]:
        if date_from.tzinfo is None or date_to.tzinfo is None:
            raise ValueError("date_from and date_to must include a timezone")
        if date_from >= date_to:
            raise ValueError("date_from must be earlier than date_to")
        if not self.available() or not self._initialize():
            return []

        timeframe_constant = getattr(self.mt5, f"TIMEFRAME_{timeframe.upper()}", None)
        if timeframe_constant is None:
            self.mt5.shutdown()
            raise ValueError(f"unsupported timeframe: {timeframe}")

        try:
            rates = self.mt5.copy_rates_range(
                symbol,
                timeframe_constant,
                date_from.astimezone(timezone.utc),
                date_to.astimezone(timezone.utc),
            )
            return self._serialize_rates(rates)
        finally:
            self.mt5.shutdown()

    def positions(self, symbol: str | None = None) -> list[dict]:
        if not self.available() or not self.mt5.initialize():
            return []
        try:
            positions = self.mt5.positions_get(symbol=symbol) if symbol else self.mt5.positions_get()
            if positions is None:
                return []
            return [
                {
                    "ticket": str(position.ticket),
                    "symbol": position.symbol,
                    "side": "BUY" if position.type == self.mt5.POSITION_TYPE_BUY else "SELL",
                    "volume": float(position.volume),
                    "price_open": float(position.price_open),
                    "price_current": float(position.price_current),
                    "stop_loss": float(position.sl),
                    "take_profit": float(position.tp),
                    "profit": float(position.profit),
                    "magic": int(position.magic),
                    "comment": position.comment,
                }
                for position in positions
            ]
        finally:
            self.mt5.shutdown()

    def order(self, payload: dict) -> dict:
        if not self.available():
            return {"success": False, "error": "MetaTrader5 package is not installed"}
        if not self.mt5.initialize():
            return {"success": False, "error": f"MT5 initialization failed: {self.mt5.last_error()}"}

        try:
            account = self.mt5.account_info()
            if account is None or account.trade_mode != self.mt5.ACCOUNT_TRADE_MODE_DEMO:
                return {"success": False, "error": "demo account is required"}

            symbol = self.mt5.symbol_info(payload["symbol"])
            if symbol is None or not symbol.visible:
                return {"success": False, "error": f"symbol is unavailable: {payload['symbol']}"}
            volume = float(payload["volume"])
            if volume < symbol.volume_min or volume > symbol.volume_max:
                return {"success": False, "error": "volume is outside broker limits"}
            steps = round((volume - symbol.volume_min) / symbol.volume_step)
            if abs(symbol.volume_min + steps * symbol.volume_step - volume) > 1e-9:
                return {"success": False, "error": "volume does not match broker step"}

            tick = self.mt5.symbol_info_tick(payload["symbol"])
            if tick is None:
                return {"success": False, "error": "symbol quote is unavailable"}
            order_type = self.mt5.ORDER_TYPE_BUY if payload["side"] == "BUY" else self.mt5.ORDER_TYPE_SELL
            price = tick.ask if order_type == self.mt5.ORDER_TYPE_BUY else tick.bid
            request = {
                "action": self.mt5.TRADE_ACTION_DEAL,
                "symbol": payload["symbol"],
                "volume": volume,
                "type": order_type,
                "price": price,
                "sl": float(payload["stop_loss"]),
                "tp": float(payload["take_profit"]),
                "deviation": int(payload.get("deviation", 20)),
                "magic": int(payload.get("magic", 1302015909)),
                "comment": payload.get("comment", "Nirv demo trade"),
                "type_time": self.mt5.ORDER_TIME_GTC,
                "type_filling": self.mt5.ORDER_FILLING_IOC,
            }
            check = self.mt5.order_check(request)
            if check is None or check.retcode != 0:
                return {
                    "success": False,
                    "error": getattr(check, "comment", "MT5 order check failed"),
                    "retcode": getattr(check, "retcode", None),
                }
            result = self.mt5.order_send(request)
            if result is None or result.retcode != self.mt5.TRADE_RETCODE_DONE:
                return {
                    "success": False,
                    "error": getattr(result, "comment", "MT5 order failed"),
                    "retcode": getattr(result, "retcode", None),
                }
            return {"success": True, "ticket": str(result.order or result.deal), "retcode": result.retcode}
        finally:
            self.mt5.shutdown()

    def close_position(self, payload: dict) -> dict:
        if not self.available() or not self.mt5.initialize():
            return {"success": False, "error": "MT5 initialization failed"}
        try:
            account = self.mt5.account_info()
            if account is None or account.trade_mode != self.mt5.ACCOUNT_TRADE_MODE_DEMO:
                return {"success": False, "error": "demo account is required"}
            positions = self.mt5.positions_get(ticket=int(payload["ticket"]))
            if not positions:
                return {"success": False, "error": "position not found"}
            position = positions[0]
            volume = float(payload["volume"])
            if volume > float(position.volume):
                return {"success": False, "error": "close volume exceeds position volume"}
            tick = self.mt5.symbol_info_tick(position.symbol)
            if tick is None:
                return {"success": False, "error": "symbol quote is unavailable"}
            is_buy = position.type == self.mt5.POSITION_TYPE_BUY
            request = {
                "action": self.mt5.TRADE_ACTION_DEAL,
                "position": position.ticket,
                "symbol": position.symbol,
                "volume": volume,
                "type": self.mt5.ORDER_TYPE_SELL if is_buy else self.mt5.ORDER_TYPE_BUY,
                "price": tick.bid if is_buy else tick.ask,
                "deviation": 20,
                "magic": int(payload.get("magic", 1302015909)),
                "comment": payload.get("comment", "Nirv demo partial close"),
                "type_time": self.mt5.ORDER_TIME_GTC,
                "type_filling": self.mt5.ORDER_FILLING_IOC,
            }
            result = self.mt5.order_send(request)
            if result is None or result.retcode != self.mt5.TRADE_RETCODE_DONE:
                return {"success": False, "error": getattr(result, "comment", "close failed")}
            return {"success": True, "ticket": str(result.deal or result.order), "retcode": result.retcode}
        finally:
            self.mt5.shutdown()

    def modify_position(self, payload: dict) -> dict:
        if not self.available() or not self.mt5.initialize():
            return {"success": False, "error": "MT5 initialization failed"}
        try:
            account = self.mt5.account_info()
            if account is None or account.trade_mode != self.mt5.ACCOUNT_TRADE_MODE_DEMO:
                return {"success": False, "error": "demo account is required"}
            positions = self.mt5.positions_get(ticket=int(payload["ticket"]))
            if not positions:
                return {"success": False, "error": "position not found"}
            request = {
                "action": self.mt5.TRADE_ACTION_SLTP,
                "position": int(payload["ticket"]),
                "symbol": payload["symbol"],
                "sl": float(payload["stop_loss"]),
                "tp": float(payload["take_profit"]),
            }
            result = self.mt5.order_send(request)
            if result is None or result.retcode != self.mt5.TRADE_RETCODE_DONE:
                return {"success": False, "error": getattr(result, "comment", "modify failed")}
            return {"success": True, "ticket": payload["ticket"], "retcode": result.retcode}
        finally:
            self.mt5.shutdown()
