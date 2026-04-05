"""Wiring зависимостей HTTP слоя."""

from __future__ import annotations

from functools import lru_cache

from src.application.facade.application_facade import ApplicationFacade
from src.infrastructure.di.composition import RuntimeContainer, build_runtime


@lru_cache(maxsize=1)
def get_runtime() -> RuntimeContainer:
    """Возвращает singleton runtime-контейнера."""

    return build_runtime()


def get_facade() -> ApplicationFacade:
    """Возвращает singleton application facade."""

    return get_runtime().facade

