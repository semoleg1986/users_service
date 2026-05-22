"""Command DTO student invites."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateStudentInviteCommand:
    """Создает invite для existing child profile."""

    student_id: str
    actor_id: str
    actor_roles: list[str]
    ttl_seconds: int = 86400
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class ConsumeStudentInviteCommand:
    """Одноразово потребляет invite token."""

    token: str
    consumer: str
