"""Wiring зависимостей HTTP слоя."""

from __future__ import annotations

from functools import lru_cache

from src.application.ports.access_token_verifier import AccessTokenVerifier
from src.application.facade.application_facade import ApplicationFacade
from src.infrastructure.di.composition import RuntimeContainer, build_runtime


@lru_cache(maxsize=1)
def get_runtime() -> RuntimeContainer:
    """Возвращает singleton runtime-контейнера."""

    return build_runtime()


def get_facade() -> ApplicationFacade:
    """Возвращает singleton application facade."""

    return get_runtime().facade


def get_access_token_verifier() -> AccessTokenVerifier:
    """Возвращает singleton verifier access token."""

    return get_runtime().access_token_verifier
