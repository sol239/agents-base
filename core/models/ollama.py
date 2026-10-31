import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field

from .model import Model


@dataclass
class OllamaModel(Model):
    request: Callable[..., dict] | None = field(default=None, repr=False, compare=False, kw_only=True)

    async def get_thinking_levels(self) -> list[str]:
        """Discover thinking controls from the server that supplied this model."""
        if self.request is None:
            raise RuntimeError("Obtain Ollama models through an OllamaProvider to discover thinking levels")
        result = await asyncio.to_thread(self.request, "/api/show", {"model": self.model_id})
        thinking = result.get("thinking")
        if thinking is None:
            return []
        if not isinstance(thinking, dict) or not isinstance(thinking.get("values"), list):
            raise RuntimeError("Ollama returned invalid thinking metadata")
        levels = []
        for value in thinking["values"]:
            if isinstance(value, bool):
                levels.append("true" if value else "false")
            elif isinstance(value, str):
                levels.append(value)
            else:
                raise RuntimeError("Ollama returned an invalid thinking level")
        return levels
