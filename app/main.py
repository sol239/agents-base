from fastapi import FastAPI

from app.api.router import api_router
from app.config import settings
from app.lifespan import lifespan
from app.middleware import register_middleware
from app.exceptions import register_exception_handlers


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    # Register middleware
    register_middleware(app)

    # Register exception handlers
    register_exception_handlers(app)

    # Register API routes
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()