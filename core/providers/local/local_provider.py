"""Base class for providers backed by local Docker Compose services."""

import asyncio
import logging
import os
import shlex
import sys
from datetime import UTC, datetime
from pathlib import Path

from core.models.model import Model
from core.models.run import Run, RunRequest, RunResult, RunStatus
from core.models.session import Session
from core.models.usage import Usage

from ..provider import Provider

logger = logging.getLogger(__name__)


def container_name(agent: str) -> str:
    """Resolve the Compose container name, preferring the shell over .env."""
    key = f"{agent.upper()}_CONTAINER_NAME"
    value = os.environ.get(key)
    if value is None:
        env_path = Path(__file__).resolve().parents[3] / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                name, separator, raw = line.partition("=")
                if separator and name.strip() == key:
                    value = " ".join(shlex.split(raw, comments=True))
    if not value:
        raise ValueError(f"Set {key} in .env or pass container=")
    return value


class LocalProvider(Provider):
    """Share asynchronous container lifecycle operations across local providers."""

    def __init__(
        self,
        *,
        container: str | None = None,
        model: Model | None = None,
        timeout: float = 300,
    ) -> None:
        self.container = container
        self.model = model
        self.timeout = timeout
        self._usages: list[Usage] = []
        self._sessions: dict[str, Session] = {}
        self._session_locks: dict[str, asyncio.Lock] = {}
        self._history: dict[str, list[dict[str, str]]] = {}

    async def get_model(self, model_id: str) -> Model:
        """Look up a model in this provider's catalog; raise KeyError if missing."""
        for model in await self.get_models():
            if model.model_id == model_id:
                return model
        raise KeyError(f"Unknown {self.name} model: {model_id}")

    async def create_session(self, model: Model, workspace_id: str) -> Session:
        """Register a session; backend conversations are created on the first run."""
        if not isinstance(model, Model):
            raise TypeError("model must be a Model instance")
        if not model.model_id.strip() or not workspace_id.strip():
            raise ValueError("model.model_id and workspace_id must be non-empty")
        if model.thinking_level is not None:
            levels = await model.get_thinking_levels()
            if model.thinking_level not in levels:
                raise ValueError(
                    f"Unsupported thinking level {model.thinking_level!r}; choose from {levels}"
                )
        session = Session(
            provider_id=self.provider_id, model=model, workspace_id=workspace_id
        )
        self._sessions[session.session_id] = session
        self._session_locks[session.session_id] = asyncio.Lock()
        self._history[session.session_id] = []
        return session

    async def get_session(self, session_id: str) -> Session:
        """Retrieve a session registered with this provider instance."""
        try:
            return self._sessions[session_id]
        except KeyError:
            raise KeyError(f"Unknown or closed session: {session_id}") from None

    def _validate_session(self, session: Session) -> None:
        if (
            session.provider_id != self.provider_id
            or self._sessions.get(session.session_id) is not session
        ):
            raise ValueError(
                "Session does not belong to this provider instance or is closed"
            )

    async def close_session(self, session: Session) -> None:
        """Release application session state after any current run finishes."""
        self._validate_session(session)
        async with self._session_locks[session.session_id]:
            self._validate_session(session)
            self._sessions.pop(session.session_id)
            self._history.pop(session.session_id)
            self._session_locks.pop(session.session_id)

    async def run(self, session: Session, request: RunRequest) -> Run:
        self._validate_session(session)
        self._validate_prompt(request.prompt)
        async with self._session_locks[session.session_id]:
            self._validate_session(session)
            run = Run(
                session_id=session.session_id,
                status=RunStatus.RUNNING,
                started_at=datetime.now(UTC),
            )
            try:
                output = await self._run_session(session, request.prompt)
                self._history[session.session_id].extend(
                    [
                        {"role": "user", "content": request.prompt},
                        {"role": "assistant", "content": output},
                    ]
                )
                run.result = RunResult(output=output)
                run.status = RunStatus.COMPLETED
            except asyncio.CancelledError:
                run.status = RunStatus.CANCELLED
                run.result = RunResult(error="Run cancelled")
                raise
            except Exception as error:
                logger.exception("Run failed for provider %s", self.provider_id)
                run.status = RunStatus.FAILED
                run.result = RunResult(error=str(error))
            finally:
                run.completed_at = datetime.now(UTC)
            return run

    async def _run_session(self, session: Session, prompt: str) -> str:
        raise NotImplementedError

    @staticmethod
    def _workspace(session: Session) -> str:
        if not session.workspace_id.startswith("/"):
            raise ValueError(
                "workspace_id must be an absolute container path for CLI providers"
            )
        return session.workspace_id

    async def _exec(
        self,
        *args: str,
        interactive: bool = False,
        timeout: float | None = None,
        workdir: str | None = None,
    ) -> str:
        command = ["docker", "exec"]
        if workdir is not None:
            command.extend(["--workdir", workdir])
        if interactive:
            command.append("-i")
            if sys.stdin.isatty() and sys.stdout.isatty():
                command.append("-t")
        command.extend([self.container or container_name(self.provider_id), *args])
        return await self._docker(*command, interactive=interactive, timeout=timeout)

    @staticmethod
    def _validate_prompt(prompt: str) -> None:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")

    async def _docker(
        self, *command: str, interactive: bool = False, timeout: float | None = None
    ) -> str:
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=None if interactive else asyncio.subprocess.DEVNULL,
                stdout=None if interactive else asyncio.subprocess.PIPE,
                stderr=None if interactive else asyncio.subprocess.PIPE,
            )
        except OSError as error:
            raise RuntimeError(f"Cannot launch {self.name}: {error}") from error
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout if timeout is None else timeout,
            )
        except (TimeoutError, asyncio.CancelledError):
            if process.returncode is None:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
            await process.communicate()
            raise
        if process.returncode:
            detail = (stderr or stdout or b"").decode(errors="replace").strip()
            raise RuntimeError(
                f"{self.name} exited with code {process.returncode}: {detail}"
            )
        return (stdout or b"").decode(errors="replace").strip()

    async def _compose(self, *args: str) -> str:
        project_dir = Path(__file__).resolve().parents[3]
        command = [
            "docker",
            "compose",
            "--project-directory",
            str(project_dir),
            "-f",
            str(project_dir / "docker-compose.yml"),
        ]
        if self.container:
            # Override the container name without modifying the process environment.
            command = [
                "env",
                f"{self.provider_id.upper()}_CONTAINER_NAME={self.container}",
                *command,
            ]
        return await self._docker(*command, *args, self.provider_id)

    async def start_container(self) -> None:
        """Create or start this provider's Compose service in the background."""
        await self._compose("up", "-d")

    async def stop_container(self) -> None:
        """Stop this provider's service, preserving its container and volumes."""
        await self._compose("stop")

    async def check_container(self) -> bool:
        """Return whether this provider's Compose service is running."""
        return bool(await self._compose("ps", "--status", "running", "-q"))
