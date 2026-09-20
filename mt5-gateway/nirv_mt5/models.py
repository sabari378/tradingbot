from pydantic import BaseModel, Field


class OrderRequest(BaseModel):
    trade_id: str
    symbol: str = "XAUUSD"
    side: str
    volume: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    take_profit: float = Field(gt=0)
    mode: str = "DEMO"
    magic: int = 1302015909
    comment: str = "Nirv demo trade"


class CloseRequest(BaseModel):
    ticket: str
    symbol: str
    volume: float = Field(gt=0)
    mode: str = "DEMO"
    magic: int = 1302015909
    comment: str = "Nirv demo partial close"


class ModifyPositionRequest(BaseModel):
    ticket: str
    symbol: str
    stop_loss: float = Field(gt=0)
    take_profit: float = Field(gt=0)
    mode: str = "DEMO"
