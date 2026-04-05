"""Доменные события агрегата ParentStudentLink."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ParentStudentLinkCreated:
    """Событие создания связи parent-student."""

    link_id: str
    parent_id: str
    student_id: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class ParentStudentLinkActivated:
    """Событие активации связи parent-student."""

    link_id: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class ParentStudentLinkRemoved:
    """Событие удаления связи parent-student."""

    link_id: str
    occurred_at: datetime

