from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class EmergencyStop:
    active: bool = False
    reason: str | None = None
    changed_at: datetime | None = None

    def engage(self, reason: str = "manual emergency stop") -> None:
        self.active = True
        self.reason = reason
        self.changed_at = datetime.now(timezone.utc)

    def reset(self) -> None:
        self.active = False
        self.reason = None
        self.changed_at = datetime.now(timezone.utc)

    def status(self) -> dict[str, str | bool | None]:
        return {
            "active": self.active,
            "reason": self.reason,
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
        }


emergency_stop = EmergencyStop()