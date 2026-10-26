from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    symbol: str = "XAUUSD"
    timeframes: list[str] = Field(default_factory=lambda: ["M5", "M15", "H1"])


class MarketSnapshot(BaseModel):
    timeframe: str
    candle_count: int
    bid: float | None = None
    ask: float | None = None
    latest_close: float | None = None
    latest_volume: float | None = None


class AnalysisResponse(BaseModel):
    symbol: str
    direction: str | None = None
    confidence: float
    entry: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    risk_reward: float | None = None
    approved_by_risk: bool
    requires_user_approval: bool = True
    agents: list[dict]
    rejection_reasons: list[str] = []
    market_data_connected: bool = False
    analyzed_at: str | None = None
    snapshot: MarketSnapshot | None = None
