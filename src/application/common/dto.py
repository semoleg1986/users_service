"""Общие DTO application-слоя users_service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class UserProfileResult:
    """DTO профиля пользователя."""

    user_id: str
    email: str
    display_name: str
    phone: str | None
    status: str
    roles: list[str]
    created_at: datetime
    updated_at: datetime
    version: int


@dataclass(frozen=True, slots=True)
class ParentStudentLinkResult:
    """DTO связи родитель-ученик."""

    link_id: str
    parent_id: str
    student_id: str
    status: str
    note: str | None
    created_at: datetime
    updated_at: datetime
    version: int

