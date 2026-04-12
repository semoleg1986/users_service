"""Конструктор FastAPI приложения."""

from __future__ import annotations

from fastapi import FastAPI

from src.interface.http.errors import register_exception_handlers
from src.interface.http.health import router as health_router
from src.interface.http.v1.admin.router import router as admin_router
from src.interface.http.v1.internal.router import router as internal_router
from src.interface.http.v1.parent.router import router as parent_router
from src.interface.http.v1.user.router import router as user_router


def create_app() -> FastAPI:
    """Создает и настраивает экземпляр FastAPI."""

    app = FastAPI(title="users_service API", version="0.1.0")
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(internal_router)
    app.include_router(admin_router)
    app.include_router(user_router)
    app.include_router(parent_router)
    return app
