from dataclasses import dataclass, field

from .model import Model


@dataclass
class AntigravityModel(Model):
    thinking_variants: dict[str, str] = field(default_factory=dict, repr=False, compare=False)

    async def get_thinking_levels(self) -> list[str]:
        """Return levels backed by model variants in the available catalog."""
        return list(self.thinking_variants)

    def execution_model_id(self) -> str:
        """Resolve an explicit thinking choice to its advertised model variant."""
        if self.thinking_level is None:
            return self.model_id
        try:
            return self.thinking_variants[self.thinking_level]
        except KeyError:
            raise ValueError(f"Unsupported thinking level: {self.thinking_level}") from None
