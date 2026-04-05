"""Репозиторный порт агрегата UserProfile."""

from __future__ import annotations

from typing import Protocol

from .entity import UserProfile


class UserProfileRepository(Protocol):
    """Контракт репозитория профилей пользователей."""

    def get(self, user_id: str) -> UserProfile | None:
        """Возвращает профиль по user_id."""

    def get_by_email(self, email: str) -> UserProfile | None:
        """Возвращает профиль по email."""

    def save(self, profile: UserProfile) -> None:
        """Сохраняет агрегат профиля пользователя."""

    def list(self, *, role: str | None = None, status: str | None = None) -> list[UserProfile]:
        """Возвращает список профилей с фильтрацией."""
