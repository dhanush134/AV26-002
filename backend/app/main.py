from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.schemas.common import MEDICAL_DISCLAIMER


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="LifeTwin AI API",
        description=(
            "Preventive healthcare digital twin backend for wellness trajectory, "
            f"risk pattern insights, and daily healthspan alignment. {MEDICAL_DISCLAIMER}"
        ),
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)

    @app.get("/health", tags=["Health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name, "environment": settings.app_env}

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
