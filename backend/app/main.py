"""FastAPI application entrypoint for LeadGen Pro."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    logging.basicConfig(
        level=logging.INFO if settings.app_env.lower() == "production" else logging.DEBUG,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    application = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router)

    @application.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """Health endpoint for monitoring and readiness checks."""
        return {"status": "ok"}

    @application.get("/test")
    def test():
        return {"status": "working"}

    @application.get("/debug")
    def debug():
        settings = get_settings()
        return {
            "google_key_exists": bool(settings.google_places_api_key)
        }

    return application


app = create_app()
