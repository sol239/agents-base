"""Codex CLI provider using the existing Docker container and saved login."""

import asyncio
import json

from .local_provider import LocalProvider, container_name
from core.models.model import Model
from core.models.codex import CodexModel
from core.models.session import Session
from core.models.usage import Usage


class CodexCLIProvider(LocalProvider):
    @property
    def usages(self) -> list[Usage]:
        """Return the latest stored quota snapshots without performing I/O."""
        return list(self._usages)

    @property
    def provider_id(self) -> str:
        return "codex"

    @property
    def name(self) -> str:
        return "Codex CLI"

    async def authenticate(self) -> None:
        if not await self.is_authenticated():
            await self._exec("codex", "login", "--device-auth", interactive=True, timeout=600)
            if not await self.is_authenticated():
                raise RuntimeError("Codex login completed without a saved authentication")

    async def is_authenticated(self) -> bool:
        try:
            await self._exec("codex", "login", "status", timeout=15)
            return True
        except (RuntimeError, ValueError, OSError, asyncio.TimeoutError):
            return False

    async def _run_session(self, session: Session, prompt: str) -> str:
        args = ["codex", "exec"]
        if session.provider_session_id:
            args.append("resume")
        args.extend(["--skip-git-repo-check", "--json", "--model", session.model.model_id])
        if session.model.thinking_level is not None:
            args.extend(["-c", "model_reasoning_effort=" + json.dumps(session.model.thinking_level)])
        args.append("--")
        if session.provider_session_id:
            args.append(session.provider_session_id)
        args.append(prompt)
        output = await self._exec(*args, workdir=self._workspace(session))
        messages = []
        completed = False
        for line in output.splitlines():
            event = json.loads(line)
            if event.get("type") == "thread.started":
                session.provider_session_id = event["thread_id"]
            elif event.get("type") == "item.completed":
                item = event.get("item", {})
                if item.get("type") == "agent_message":
                    messages.append(item["text"])
            elif event.get("type") in ("error", "turn.failed"):
                raise RuntimeError(f"Codex run failed: {event}")
            elif event.get("type") == "turn.completed":
                completed = True
        if not completed or not session.provider_session_id:
            raise RuntimeError("Codex did not return a completed turn and conversation ID")
        return "\n".join(messages)

    async def get_models(self) -> list[Model]:
        """Read the paginated catalog through Codex's stdio app-server API."""
        process = await asyncio.create_subprocess_exec(
            "docker", "exec", "-i", self.container or container_name(self.provider_id),
            "codex", "app-server",
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stderr_task = asyncio.create_task(process.stderr.read())

        async def send(message: dict) -> None:
            process.stdin.write((json.dumps(message) + "\n").encode())
            await process.stdin.drain()

        async def request(request_id: int, method: str, params: dict) -> dict:
            await send({"id": request_id, "method": method, "params": params})
            while line := await process.stdout.readline():
                message = json.loads(line)
                if message.get("id") != request_id:
                    continue
                if "error" in message:
                    raise RuntimeError(f"Codex {method} failed: {message['error']}")
                return message["result"]
            raise RuntimeError("Codex app-server closed before returning its model list")

        try:
            async with asyncio.timeout(self.timeout):
                await request(1, "initialize", {
                    "clientInfo": {"name": "agents-base", "version": "1.0.0"},
                })
                await send({"method": "initialized"})
                models = []
                cursor = None
                request_id = 2
                seen_cursors = set()
                while True:
                    result = await request(request_id, "model/list", {"cursor": cursor})
                    for row in result["data"]:
                        models.append(CodexModel(
                            model_id=row["model"], name=row["displayName"],
                            supported_thinking_levels=tuple(
                                option["reasoningEffort"] for option in row.get("supportedReasoningEfforts", [])
                            ),
                        ))
                    cursor = result.get("nextCursor")
                    if not cursor:
                        return models
                    if cursor in seen_cursors:
                        raise RuntimeError("Codex returned a repeated model-list cursor")
                    seen_cursors.add(cursor)
                    request_id += 1
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeError("Codex returned an invalid model list") from error
        finally:
            if process.returncode is None:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
            await process.wait()
            await stderr_task
