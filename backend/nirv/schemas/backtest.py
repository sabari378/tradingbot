from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class BacktestRequest(BaseModel):
    symbol: str = "GOLD.i#"
    timeframe: Literal["M5", "M15", "H1"] = "M15"
    date_from: datetime
    date_to: datetime
    strategy: Literal[
        "confluence",
        "sma_crossover",
        "donchian_breakout",
        "bollinger_reversion",
        "rsi_countertrend",
        "volatility_breakout",
        "engulfing_reversal",
        "market_structure",
        "liquidity_sweep",
        "fair_value_gap",
        "double_top",
    ] = "confluence"
    signals: list[Literal["liquidity", "mss", "fvg"]] = Field(default_factory=lambda: ["liquidity", "fvg"])
    require_volume: bool = False
    risk_reward: float = Field(default=2.0, ge=1.0, le=5.0)

    @field_validator("date_from", "date_to")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timezone is required")
        return value

    @field_validator("signals")
    @classmethod
    def require_signals(cls, value: list[str]) -> list[str]:
        unique = list(dict.fromkeys(value))
        if not unique:
            raise ValueError("at least one signal is required")
        return unique

    @model_validator(mode="after")
    def validate_range(self) -> "BacktestRequest":
        if self.date_from >= self.date_to:
            raise ValueError("date_from must be earlier than date_to")
        if (self.date_to - self.date_from).days > 366:
            raise ValueError("backtest range cannot exceed 366 days")
        return self


class BacktestTrade(BaseModel):
    direction: Literal["BUY", "SELL"]
    signal_time: datetime
    entry_time: datetime
    exit_time: datetime
    entry: float
    stop_loss: float
    take_profit: float
    exit: float
    exit_reason: Literal["STOP_LOSS", "TAKE_PROFIT", "SESSION_END"]
    pnl_points: float
    pnl_r: float
    confluences: list[str]


class BacktestMetrics(BaseModel):
    candles: int
    signals: int
    rejected_entries: int
    trades: int
    wins: int
    losses: int
    win_rate: float
    net_pnl_points: float
    expectancy_r: float
    profit_factor: float | None
    max_drawdown_r: float


class BacktestResponse(BaseModel):
    agent: str = "backtest"
    display_name: str = "Chronos"
    symbol: str
    timeframe: str
    date_from: datetime
    date_to: datetime
    strategy: dict[str, object]
    metrics: BacktestMetrics
    trades: list[BacktestTrade]
    warnings: list[str]
