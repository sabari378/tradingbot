from dataclasses import dataclass


@dataclass(frozen=True)
class SymbolSpecification:
    symbol: str
    contract_size: float
    volume_step: float = 0.01
    min_volume: float = 0.01


@dataclass(frozen=True)
class PositionSize:
    volume: float
    risk_amount: float


def calculate_position_size(
    balance: float, risk_percent: float, entry: float, stop_loss: float, specification: SymbolSpecification
) -> PositionSize:
    distance = abs(entry - stop_loss)
    if distance <= 0:
        raise ValueError("zero stop distance")
    risk_amount = balance * risk_percent / 100
    raw_volume = risk_amount / (distance * specification.contract_size)
    steps = int(raw_volume / specification.volume_step)
    volume = max(specification.min_volume, steps * specification.volume_step)
    return PositionSize(volume=round(volume, 2), risk_amount=round(risk_amount, 2))
