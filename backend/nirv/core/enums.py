from enum import StrEnum


class TradeDirection(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class TradeStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SENT = "SENT"
    FILLED = "FILLED"
    FAILED = "FAILED"
    CLOSED = "CLOSED"


class ExecutionMode(StrEnum):
    PAPER = "PAPER"
    DEMO = "DEMO"


class AgentStatus(StrEnum):
    COMPLETED = "completed"
    UNAVAILABLE = "unavailable"
