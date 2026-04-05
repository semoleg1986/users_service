"""Доменные события агрегата UserProfile."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class UserCreated:
    """Событие создания пользователя."""

    user_id: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class UserRoleChanged:
    """Событие изменения ролевого набора пользователя."""

    user_id: str
    role: str
    action: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class UserStatusChanged:
    """Событие смены статуса пользователя."""

    user_id: str
    status: str
    occurred_at: datetime

