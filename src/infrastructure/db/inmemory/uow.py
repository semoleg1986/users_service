"""In-memory Unit of Work."""

from __future__ import annotations

from dataclasses import dataclass

from src.application.ports.repositories import RepositoryProvider
from src.infrastructure.db.inmemory.repositories import (
    InMemoryParentStudentLinkRepository,
    InMemoryUserProfileRepository,
)


@dataclass(frozen=True, slots=True)
class InMemoryRepositoryProvider(RepositoryProvider):
    """Набор in-memory репозиториев users_service."""

    user_profiles: InMemoryUserProfileRepository
    parent_student_links: InMemoryParentStudentLinkRepository


class InMemoryUnitOfWork:
    """In-memory реализация UoW."""

    def __init__(self, repositories: InMemoryRepositoryProvider) -> None:
        self.repositories = repositories

    def __enter__(self) -> InMemoryUnitOfWork:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc is not None:
            self.rollback()

    def commit(self) -> None:
        """Для in-memory фиксация не требуется."""

    def rollback(self) -> None:
        """Для in-memory откат не поддерживается."""
