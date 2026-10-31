"""Antigravity CLI provider using the existing Docker container."""

import json
import sys
from datetime import datetime

from core.models.antigravity import AntigravityModel
from core.models.model import Model
from core.models.session import Session
from core.models.usage import Usage

from .local_provider import LocalProvider


class AntigravityCLIProvider(LocalProvider):
    @property
    def usages(self) -> list[Usage]:
        """Return the latest stored quota snapshots without performing I/O."""
        return list(self._usages)

    async def refresh_usages(self) -> list[Usage]:
        """Run the local /usage command; this does not submit a model prompt."""
        output = await self._exec(
            "agy", "--output-format", "json", "--print", "/usage", timeout=30
        )
        usages = self._parse_usages(json.loads(output))
        self._usages = usages
        return self.usages

    @staticmethod
    def _parse_usages(result: dict) -> list[Usage]:
        if result.get("status") != "SUCCESS" or result.get("command", {}).get(
            "name"
        ) not in ("usage", "quota"):
            raise RuntimeError(
                "Antigravity did not return a successful usage command result"
            )
        usages = []
        try:
            for group in result["command"]["data"]["groups"]:
                for bucket in group["buckets"]:
                    usages.append(
                        Usage(
                            name=f"{group['name']} / {bucket['name']}",
                            value=1 - float(bucket["remaining_fraction"]),
                            resets_at=datetime.fromisoformat(bucket["reset_time"]),
                        )
                    )
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            raise RuntimeError("Antigravity returned invalid quota data") from error
        return usages

    @property
    def provider_id(self) -> str:
        return "antigravity"

    @property
    def name(self) -> str:
        return "Antigravity CLI"

    async def authenticate(self) -> None:
        if await self.is_authenticated():
            return
        if not (sys.stdin.isatty() and sys.stdout.isatty()):
            raise RuntimeError(
                "Antigravity sign-in requires calling authenticate() from an interactive terminal"
            )
        await self._exec("agy", interactive=True, timeout=600)
        if not await self.is_authenticated():
            raise RuntimeError("Antigravity session ended without authentication")

    async def is_authenticated(self) -> bool:
        try:
            await self._exec("agy", "models", timeout=15)
            return True
        except (TimeoutError, RuntimeError, ValueError, OSError):
            return False

    async def _run_session(self, session: Session, prompt: str) -> str:
        # Print mode has no documented machine-readable conversation ID contract.
        # Keep history per application session instead of resuming the global latest chat.
        history = self._history[session.session_id]
        if history:
            prompt = (
                "Continue this conversation. Previous messages (JSON):\n"
                + json.dumps(history)
                + "\n\nCurrent user message:\n"
                + prompt
            )
        if not isinstance(session.model, AntigravityModel):
            raise TypeError("Antigravity sessions require an AntigravityModel")
        args = [
            "agy",
            "--output-format",
            "text",
            "--model",
            session.model.execution_model_id(),
        ]
        return await self._exec(
            *args,
            "--print",
            prompt,
            workdir=self._workspace(session),
        )

    async def get_models(self) -> list[Model]:
        """Parse the tab-separated catalog returned by agy models."""
        output = await self._exec("agy", "models", timeout=30)
        models = []
        for line in output.splitlines():
            if not line.strip() or line.strip() == "Fetching available models...":
                continue
            model_id, separator, name = line.partition("\t")
            if not separator or not model_id.strip() or not name.strip():
                raise RuntimeError("Antigravity returned an invalid model list")
            models.append(
                AntigravityModel(model_id=model_id.strip(), name=name.strip())
            )
        # Gemini's available thinking choices are exposed as separate model IDs.
        families: dict[str, dict[str, str]] = {}
        for model in models:
            family, _, level = model.model_id.rpartition("-")
            if family.startswith("gemini-") and level in ("low", "medium", "high"):
                families.setdefault(family, {})[level] = model.model_id
        for model in models:
            family, _, _ = model.model_id.rpartition("-")
            variants = families.get(family, {})
            model.thinking_variants = {
                level: variants[level]
                for level in ("low", "medium", "high")
                if level in variants
            }
        return models
