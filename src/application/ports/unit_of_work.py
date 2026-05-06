"""Порт Unit of Work."""

from __future__ import annotations

from typing import Callable, Protocol

from src.application.ports.repositories import RepositoryProvider


class UnitOfWork(Protocol):
    """Контракт транзакционной границы application-слоя."""

    repositories: RepositoryProvider

    def commit(self) -> None:
        """Фиксирует изменения."""

    def rollback(self) -> None:
        """Откатывает изменения."""


UnitOfWorkFactory = Callable[[], UnitOfWork]
