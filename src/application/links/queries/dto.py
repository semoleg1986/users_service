"""Query DTO для связей parent-student."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ListParentStudentLinksQuery:
    """Возвращает список связей parent-student."""

    actor_id: str
    actor_roles: list[str]
    parent_id: str | None = None
    student_id: str | None = None
