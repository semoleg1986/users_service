"""Query DTO профиля пользователя."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetUserByIdQuery:
    """Получает профиль пользователя по ID."""

    user_id: str
    actor_id: str
    actor_roles: list[str]


@dataclass(frozen=True, slots=True)
class ListUsersQuery:
    """Возвращает список профилей пользователей."""

    actor_id: str
    actor_roles: list[str]
    role: str | None = None
    status: str | None = None


@dataclass(frozen=True, slots=True)
class GetMyProfileQuery:
    """Возвращает профиль текущего пользователя."""

    actor_id: str
    actor_roles: list[str]


@dataclass(frozen=True, slots=True)
class ListParentStudentsQuery:
    """Возвращает список учеников, связанных с parent."""

    actor_id: str
    actor_roles: list[str]
    limit: int = 20
    offset: int = 0
    sort: str = "created_at:asc"
