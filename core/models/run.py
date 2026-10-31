from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from .generate_id import generate_id


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class RunRequest:
    prompt: str


@dataclass(frozen=True)
class RunResult:
    output: str | None = None
    error: str | None = None


@dataclass
class Run:
    session_id: str
    run_id: str = field(default_factory=lambda: generate_id("run"))
    status: RunStatus = RunStatus.QUEUED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: RunResult | None = None
