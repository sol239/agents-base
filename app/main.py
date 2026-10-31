from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    return FastAPI()


app = create_app()
