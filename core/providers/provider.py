from abc import ABC, abstractmethod

from core.models.model import Model
from core.models.session import Session
from core.models.run import Run, RunRequest
from core.models.usage import Usage


class Provider(ABC):
    """Abstract base class for agent providers."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique provider identifier."""
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        raise NotImplementedError

    @property
    @abstractmethod
    def usages(self) -> list[Usage]:
        """Known usage snapshots; empty when unavailable or not applicable."""
        raise NotImplementedError

    @abstractmethod
    async def authenticate(self) -> None:
        """Authenticate with the provider."""
        raise NotImplementedError

    @abstractmethod
    async def is_authenticated(self) -> bool:
        """Check whether the provider is authenticated."""
        raise NotImplementedError

    @abstractmethod
    async def get_models(self) -> list[Model]:
        """Get available models."""
        raise NotImplementedError

    @abstractmethod
    async def get_model(self, model_id: str) -> Model:
        """Get an available model by ID; raise KeyError if it is unknown."""
        raise NotImplementedError

    @abstractmethod
    async def create_session(
        self,
        model: Model,
        workspace_id: str,
    ) -> Session:
        """Create a new agent session."""
        raise NotImplementedError

    @abstractmethod
    async def get_session(
        self,
        session_id: str,
    ) -> Session:
        """Retrieve an existing session."""
        raise NotImplementedError

    @abstractmethod
    async def close_session(
        self,
        session: Session,
    ) -> None:
        """Close a session and release provider resources."""
        raise NotImplementedError

    @abstractmethod
    async def run(
        self,
        session: Session,
        request: RunRequest,
    ) -> Run:
        """Execute an agent task within a session."""
        raise NotImplementedError
