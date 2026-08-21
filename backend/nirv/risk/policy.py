from dataclasses import dataclass

from nirv.core.config import Settings
from nirv.core.enums import TradeDirection
from nirv.risk.calculator import SymbolSpecification


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reasons: list[str]


def evaluate_risk(
    *,
    direction: TradeDirection,
    entry: float,
    stop_loss: float,
    take_profit: float,
    risk_percent: float,
    daily_loss_percent: float,
    open_trades: int,
    spread: float,
    data_age_seconds: int,
    news_blocked: bool,
    settings: Settings,
) -> RiskDecision:
    reasons: list[str] = []
    stop_distance = abs(entry - stop_loss)
    reward = abs(take_profit - entry)
    rr = reward / stop_distance if stop_distance else 0
    valid_stop = (direction == TradeDirection.BUY and stop_loss < entry) or (
        direction == TradeDirection.SELL and stop_loss > entry
    )
    if not valid_stop or stop_distance == 0:
        reasons.append("invalid_stop")
    if risk_percent > settings.max_risk_percent:
        reasons.append("risk_too_high")
    if rr < settings.min_risk_reward:
        reasons.append("insufficient_risk_reward")
    if daily_loss_percent >= settings.max_daily_loss_percent:
        reasons.append("daily_loss_limit_exceeded")
    if open_trades >= settings.max_open_trades:
        reasons.append("maximum_open_trades_exceeded")
    if spread > settings.max_spread:
        reasons.append("spread_too_high")
    if data_age_seconds > settings.max_signal_age_seconds:
        reasons.append("stale_market_data")
    if news_blocked:
        reasons.append("news_blackout")
    return RiskDecision(approved=not reasons, reasons=reasons)


DEFAULT_XAUUSD_SPECIFICATION = SymbolSpecification(symbol="XAUUSD", contract_size=100)
