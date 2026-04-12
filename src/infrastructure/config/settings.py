"""Настройки запуска users_service."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    """Параметры runtime-конфигурации."""

    database_url: str
    use_inmemory: bool
    auto_create_schema: bool
    auth_jwks_url: str
    auth_jwks_json: str | None
    auth_issuer: str
    auth_audience: str
    service_token: str

    @classmethod
    def from_env(cls) -> "Settings":
        """Читает настройки из переменных окружения."""

        return cls(
            database_url=os.getenv(
                "USERS_DATABASE_URL", "sqlite:///./users_service.db"
            ),
            use_inmemory=os.getenv("USERS_USE_INMEMORY", "1") == "1",
            auto_create_schema=os.getenv("USERS_AUTO_CREATE_SCHEMA", "0") == "1",
            auth_jwks_url=os.getenv(
                "USERS_AUTH_JWKS_URL",
                "http://localhost:8000/.well-known/jwks.json",
            ),
            auth_jwks_json=os.getenv("USERS_AUTH_JWKS_JSON"),
            auth_issuer=os.getenv("USERS_AUTH_ISSUER", "auth_service"),
            auth_audience=os.getenv("USERS_AUTH_AUDIENCE", "platform_clients"),
            service_token=os.getenv("USERS_SERVICE_TOKEN", "dev-service-token"),
        )
