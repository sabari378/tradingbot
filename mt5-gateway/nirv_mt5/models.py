from pydantic import BaseModel, Field


class OrderRequest(BaseModel):
    trade_id: str
    symbol: str = "XAUUSD"
    side: str
    volume: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    take_profit: float = Field(gt=0)
    mode: str = "DEMO"


class CloseRequest(BaseModel):
    ticket: str
