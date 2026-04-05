"""Command DTO для связей parent-student."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateParentStudentLinkCommand:
    """Создает связь parent-student."""

    link_id: str | None
    parent_id: str
    student_id: str
    actor_id: str
    actor_roles: list[str]
    note: str | None = None


@dataclass(frozen=True, slots=True)
class RemoveParentStudentLinkCommand:
    """Удаляет связь parent-student."""

    link_id: str
    actor_id: str
    actor_roles: list[str]
