from dataclasses import dataclass, field

from .model import Model


@dataclass
class CodexModel(Model):
    supported_thinking_levels: tuple[str, ...] = field(default=(), repr=False, compare=False)

    async def get_thinking_levels(self) -> list[str]:
        """Return the effort choices advertised in the Codex model catalog."""
        return list(self.supported_thinking_levels)
