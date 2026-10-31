from dataclasses import dataclass, field
from datetime import UTC, datetime

from .generate_id import generate_id
from .model import Model


@dataclass
class Session:
    provider_id: str
    model: Model
    session_id: str = field(default_factory=lambda: generate_id("session"))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    provider_session_id: str | None = None
    workspace_id: str = "/workspace"
