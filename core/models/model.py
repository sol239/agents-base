from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from .generate_id import generate_id


@dataclass()
class Model(ABC):
    name: str
    model_id: str = field(default_factory=lambda: generate_id("model"))
    thinking_level: str | None = None

    @abstractmethod
    async def get_thinking_levels(self) -> list[str]:
        """Return supported thinking levels; None selects the backend default."""
        raise NotImplementedError
