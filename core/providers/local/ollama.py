"""Ollama provider. Local Ollama requires no login or API key."""

import asyncio
import json
import os
import urllib.error
import urllib.request

from core.models.model import Model
from core.models.ollama import OllamaModel
from core.models.session import Session
from core.models.usage import Usage

from .local_provider import LocalProvider


class OllamaProvider(LocalProvider):
    @property
    def usages(self) -> list[Usage]:
        """Local Ollama does not expose account quota usage."""
        return []

    async def refresh_usages(self) -> list[Usage]:
        return []

    def __init__(
        self,
        model: Model | None = None,
        *,
        base_url: str | None = None,
        timeout: float = 300,
        container: str | None = None,
    ) -> None:
        env_model = os.environ.get("OLLAMA_MODEL")
        super().__init__(
            container=container,
            model=model
            or (
                OllamaModel(
                    name=env_model,
                    model_id=env_model,
                    request=lambda *args, **kwargs: self._request(*args, **kwargs),
                )
                if env_model
                else None
            ),
            timeout=timeout,
        )
        self.base_url = (
            base_url or os.environ.get("OLLAMA_HOST") or "http://localhost:11434"
        ).rstrip("/")
        if "://" not in self.base_url:
            self.base_url = "http://" + self.base_url
        self.timeout = timeout

    @property
    def provider_id(self) -> str:
        return "ollama"

    @property
    def name(self) -> str:
        return "Ollama"

    def _request(
        self, path: str, payload: dict | None = None, timeout: float | None = None
    ) -> dict:
        request = urllib.request.Request(
            self.base_url + path,
            data=None if payload is None else json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(
                request, timeout=self.timeout if timeout is None else timeout
            ) as response:
                result = json.load(response)
        except urllib.error.HTTPError as error:
            detail = error.read().decode(errors="replace")
            raise RuntimeError(f"Ollama HTTP {error.code}: {detail}") from error
        except (OSError, ValueError) as error:
            raise RuntimeError(f"Ollama request failed: {error}") from error
        if not isinstance(result, dict):
            raise TypeError("Ollama returned an invalid response")
        if result.get("error"):
            raise RuntimeError(f"Ollama: {result['error']}")
        return result

    async def authenticate(self) -> None:
        """Verify connectivity; local Ollama has no authentication flow."""
        await asyncio.to_thread(self._request, "/api/version", timeout=15)

    async def get_models(self) -> list[Model]:
        """List models installed on this Ollama server."""
        result = await asyncio.to_thread(self._request, "/api/tags", timeout=15)
        try:
            rows = result["models"]
            if not isinstance(rows, list):
                raise TypeError("models must be a list")
            models: list[Model] = [
                OllamaModel(
                    model_id=row["model"],
                    name=row["name"],
                    request=lambda *args, **kwargs: self._request(*args, **kwargs),
                )
                for row in rows
            ]
            if any(
                not isinstance(m.model_id, str) or not isinstance(m.name, str)
                for m in models
            ):
                raise ValueError("invalid model fields")
            return models
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeError("Ollama returned an invalid model list") from error

    async def is_authenticated(self) -> bool:
        try:
            await self.authenticate()
            return True
        except (RuntimeError, TypeError):
            return False

    async def _run_session(self, session: Session, prompt: str) -> str:
        payload = {
            "model": session.model.model_id,
            "messages": [
                *self._history[session.session_id],
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        level = session.model.thinking_level
        if level is not None:
            payload["think"] = {"true": True, "false": False}.get(level, level)
        result = await asyncio.to_thread(
            self._request,
            "/api/chat",
            payload,
        )
        message = result.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise TypeError("Ollama response is missing the generated text")
        return message["content"]
