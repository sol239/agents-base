from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class Usage:
    """A consumed quota fraction (0.5 means 50%) and its UTC reset time."""

    name: str
    value: float
    resets_at: datetime

    def __post_init__(self) -> None:
        if not 0 <= self.value <= 1:
            raise ValueError("Usage value must be between 0 and 1")
        if self.resets_at.utcoffset() is None:
            raise ValueError("Usage resets_at must be timezone-aware")
        object.__setattr__(self, "resets_at", self.resets_at.astimezone(UTC))
