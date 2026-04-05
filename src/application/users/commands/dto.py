"""Command DTO профиля пользователя."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateUserProfileCommand:
    """Создает профиль пользователя."""

    user_id: str | None
    email: str
    display_name: str
    phone: str | None
    roles: list[str]
    actor_id: str


@dataclass(frozen=True, slots=True)
class UpdateUserProfileCommand:
    """Обновляет профиль пользователя."""

    user_id: str
    actor_id: str
    actor_roles: list[str]
    display_name: str | None = None
    email: str | None = None
    phone: str | None = None


@dataclass(frozen=True, slots=True)
class AssignRoleCommand:
    """Назначает роль пользователю."""

    user_id: str
    role: str
    actor_id: str
    actor_roles: list[str]


@dataclass(frozen=True, slots=True)
class RevokeRoleCommand:
    """Снимает роль у пользователя."""

    user_id: str
    role: str
    actor_id: str
    actor_roles: list[str]


@dataclass(frozen=True, slots=True)
class ChangeUserStatusCommand:
    """Изменяет статус пользователя."""

    user_id: str
    action: str  # block | unblock | archive | restore
    actor_id: str
    actor_roles: list[str]
