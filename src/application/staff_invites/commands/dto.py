"""Command DTO staff invites."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateStaffInviteCommand:
    """Создает invite для existing studio/admin profile."""

    target_user_id: str
    actor_id: str
    actor_roles: list[str]
    roles: list[str] | None = None
    ttl_seconds: int = 86400
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class ConsumeStaffInviteCommand:
    """Одноразово потребляет staff invite token."""

    token: str
    consumer: str
