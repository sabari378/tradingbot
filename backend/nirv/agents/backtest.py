from datetime import datetime, timezone
from typing import Any

from nirv.agents.base import BaseAgent
from nirv.market.candles import Candle
from nirv.schemas.agent import AgentResult
from nirv.schemas.backtest import BacktestMetrics, BacktestRequest, BacktestResponse, BacktestTrade
from nirv.strategies.catalog import evaluate_catalog_strategy
from nirv.strategies.setup import SetupDecision, analyze_setup


class BacktestAgent(BaseAgent):
    name = "backtest"
    display_name = "Chronos"
    minimum_history = 25
    rolling_window = 200

    async def analyze(self, context: dict[str, Any]) -> AgentResult:
        candle_count = len(context.get("candles", []))
        return AgentResult(
            agent=self.name,
            confidence=1.0 if candle_count >= self.minimum_history else 0.0,
            reasoning_summary=f"Chronological replay is ready for {candle_count} historical candles.",
            features={"candles": candle_count, "future_trade_monitoring": "planned"},
        )

    def run(
        self,
        request: BacktestRequest,
        raw_candles: list[dict[str, Any]],
        *,
        point: float,
    ) -> BacktestResponse:
        candles = [self._candle(item) for item in raw_candles]
        trades: list[BacktestTrade] = []
        position: dict[str, Any] | None = None
        pending: tuple[SetupDecision, datetime] | None = None
        signal_count = 0
        rejected_entries = 0

        for index, candle in enumerate(candles):
            raw = raw_candles[index]
            candle_time = self._time(raw["time"])
            spread = max(0.0, float(raw.get("spread", 0)) * point)

            if position is not None:
                closed = self._close_position(position, candle, candle_time, spread)
                if closed is not None:
                    trades.append(closed)
                    position = None

            if position is None and pending is not None:
                decision, signal_time = pending
                position = self._open_position(decision, candle, candle_time, signal_time, spread, request.risk_reward)
                if position is None:
                    rejected_entries += 1
                else:
                    closed = self._close_position(position, candle, candle_time, spread)
                    if closed is not None:
                        trades.append(closed)
                        position = None
                pending = None

            history_start = max(0, index + 1 - self.rolling_window)
            if position is None and index + 1 >= self.minimum_history:
                window = candles[history_start : index + 1]
                decision = (
                    analyze_setup(
                        window,
                        news_blocked=False,
                        risk_reward=request.risk_reward,
                        use_liquidity="liquidity" in request.signals,
                        use_mss="mss" in request.signals,
                        use_fvg="fvg" in request.signals,
                        use_volume=request.require_volume,
                        require_volume=request.require_volume,
                        stop_method="structure",
                    )
                    if request.strategy == "confluence"
                    else evaluate_catalog_strategy(
                        request.strategy,
                        window,
                        risk_reward=request.risk_reward,
                        require_volume=request.require_volume,
                    )
                )
                if decision.confluence.direction:
                    signal_count += 1
                    pending = (decision, candle_time)

        if position is not None:
            final = candles[-1]
            final_raw = raw_candles[-1]
            spread = max(0.0, float(final_raw.get("spread", 0)) * point)
            trades.append(self._session_end(position, final, self._time(final_raw["time"]), spread))

        return BacktestResponse(
            symbol=request.symbol,
            timeframe=request.timeframe,
            date_from=request.date_from,
            date_to=request.date_to,
            strategy={
                "name": request.strategy,
                "signals": request.signals,
                "require_volume": request.require_volume,
                "risk_reward": request.risk_reward,
                "entry": "next_candle_open",
                "same_candle_policy": "stop_first",
            },
            metrics=self._metrics(len(candles), signal_count, rejected_entries, trades),
            trades=trades,
            warnings=[
                "MT5 bars are replayed from completed candles; intrabar price order is unavailable.",
                "If stop and target occur in one candle, the stop is applied first.",
                "Results exclude commission and slippage; recorded XM spread is included.",
            ],
        )

    @staticmethod
    def _candle(item: dict[str, Any]) -> Candle:
        return Candle(
            open=float(item["open"]),
            high=float(item["high"]),
            low=float(item["low"]),
            close=float(item["close"]),
            volume=float(item.get("volume", 0)),
        )

    @staticmethod
    def _time(value: int | float | str) -> datetime:
        if isinstance(value, str):
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        return datetime.fromtimestamp(float(value), tz=timezone.utc)

    @staticmethod
    def _open_position(
        decision: SetupDecision,
        candle: Candle,
        entry_time: datetime,
        signal_time: datetime,
        spread: float,
        risk_reward: float,
    ) -> dict[str, Any] | None:
        direction = decision.confluence.direction
        if direction is None or decision.stop_loss is None:
            return None
        entry = candle.open + spread if direction == "BUY" else candle.open
        stop_loss = float(decision.stop_loss)
        risk = entry - stop_loss if direction == "BUY" else stop_loss - entry
        if risk <= 0:
            return None
        take_profit = entry + risk * risk_reward if direction == "BUY" else entry - risk * risk_reward
        return {
            "direction": direction,
            "signal_time": signal_time,
            "entry_time": entry_time,
            "entry": entry,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk": risk,
            "confluences": decision.confluence.confluences,
        }

    @staticmethod
    def _close_position(
        position: dict[str, Any], candle: Candle, exit_time: datetime, spread: float
    ) -> BacktestTrade | None:
        if position["direction"] == "BUY":
            if candle.low <= position["stop_loss"]:
                return BacktestAgent._trade(position, exit_time, position["stop_loss"], "STOP_LOSS")
            if candle.high >= position["take_profit"]:
                return BacktestAgent._trade(position, exit_time, position["take_profit"], "TAKE_PROFIT")
        else:
            ask_high, ask_low = candle.high + spread, candle.low + spread
            if ask_high >= position["stop_loss"]:
                return BacktestAgent._trade(position, exit_time, position["stop_loss"], "STOP_LOSS")
            if ask_low <= position["take_profit"]:
                return BacktestAgent._trade(position, exit_time, position["take_profit"], "TAKE_PROFIT")
        return None

    @staticmethod
    def _session_end(position: dict[str, Any], candle: Candle, exit_time: datetime, spread: float) -> BacktestTrade:
        exit_price = candle.close if position["direction"] == "BUY" else candle.close + spread
        return BacktestAgent._trade(position, exit_time, exit_price, "SESSION_END")

    @staticmethod
    def _trade(position: dict[str, Any], exit_time: datetime, exit_price: float, reason: str) -> BacktestTrade:
        pnl = exit_price - position["entry"] if position["direction"] == "BUY" else position["entry"] - exit_price
        return BacktestTrade(
            direction=position["direction"],
            signal_time=position["signal_time"],
            entry_time=position["entry_time"],
            exit_time=exit_time,
            entry=round(position["entry"], 8),
            stop_loss=round(position["stop_loss"], 8),
            take_profit=round(position["take_profit"], 8),
            exit=round(exit_price, 8),
            exit_reason=reason,
            pnl_points=round(pnl, 8),
            pnl_r=round(pnl / position["risk"], 4),
            confluences=position["confluences"],
        )

    @staticmethod
    def _metrics(
        candle_count: int,
        signal_count: int,
        rejected_entries: int,
        trades: list[BacktestTrade],
    ) -> BacktestMetrics:
        pnl = [trade.pnl_points for trade in trades]
        pnl_r = [trade.pnl_r for trade in trades]
        wins = sum(value > 0 for value in pnl)
        losses = sum(value < 0 for value in pnl)
        gross_profit_r = sum(value for value in pnl_r if value > 0)
        gross_loss_r = abs(sum(value for value in pnl_r if value < 0))
        equity = peak = drawdown = 0.0
        for value in pnl_r:
            equity += value
            peak = max(peak, equity)
            drawdown = max(drawdown, peak - equity)
        return BacktestMetrics(
            candles=candle_count,
            signals=signal_count,
            rejected_entries=rejected_entries,
            trades=len(trades),
            wins=wins,
            losses=losses,
            win_rate=round(wins / len(trades), 4) if trades else 0,
            net_pnl_points=round(sum(pnl), 4),
            expectancy_r=round(sum(pnl_r) / len(trades), 4) if trades else 0,
            profit_factor=round(gross_profit_r / gross_loss_r, 4) if gross_loss_r else None,
            max_drawdown_r=round(drawdown, 4),
        )
