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


@dataclass(frozen=True, slots=True)
class StudentInviteResult:
    """DTO student invite."""

    invite_id: str
    parent_user_id: str
    student_user_id: str
    email: str
    status: str
    expires_at: datetime
    used_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime
    updated_at: datetime
    version: int
    invite_token: str | None = None


@dataclass(frozen=True, slots=True)
class ConsumedStudentInviteResult:
    """DTO результата consume invite use-case."""

    invite_id: str
    parent_user_id: str
    student_user_id: str
    email: str
    consumed_at: datetime
