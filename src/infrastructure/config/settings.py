"""Настройки запуска users_service."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class Settings:
    """Параметры runtime-конфигурации."""

    database_url: str
    use_inmemory: bool
    auto_create_schema: bool

    @classmethod
    def from_env(cls) -> "Settings":
        """Читает настройки из переменных окружения."""

        return cls(
            database_url=os.getenv(
                "USERS_DATABASE_URL", "sqlite:///./users_service.db"
            ),
            use_inmemory=os.getenv("USERS_USE_INMEMORY", "1") == "1",
            auto_create_schema=os.getenv("USERS_AUTO_CREATE_SCHEMA", "0") == "1",
        )

