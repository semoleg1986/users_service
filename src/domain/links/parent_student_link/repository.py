"""Репозиторный порт агрегата ParentStudentLink."""

from __future__ import annotations

from typing import Protocol

from .entity import ParentStudentLink


class ParentStudentLinkRepository(Protocol):
    """Контракт репозитория связей parent-student."""

    def get(self, link_id: str) -> ParentStudentLink | None:
        """Возвращает связь по link_id."""

    def get_active_by_pair(self, parent_id: str, student_id: str) -> ParentStudentLink | None:
        """Возвращает активную связь по паре parent-student."""

    def save(self, link: ParentStudentLink) -> None:
        """Сохраняет агрегат связи."""

