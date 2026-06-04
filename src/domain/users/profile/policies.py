"""Доменные политики доступа users/profile."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.errors import AccessDeniedError
from src.domain.shared.statuses import UserRole


@dataclass(frozen=True, slots=True)
class ActorContext:
    """Контекст актора, выполняющего операцию."""

    actor_id: str
    roles: set[UserRole]

    @classmethod
    def from_claims(cls, actor_id: str, roles: list[str]) -> "ActorContext":
        """Создает ActorContext из токенных claims."""

        return cls(actor_id=actor_id, roles={UserRole(role) for role in roles})


class AdminPolicy:
    """Политика прав администратора."""

    @staticmethod
    def ensure_can_manage_users(actor: ActorContext) -> None:
        """Проверяет право управления пользователями."""

        if UserRole.ADMIN not in actor.roles:
            raise AccessDeniedError("Операция доступна только администратору.")


class SelfServicePolicy:
    """Политика self-service операций профиля."""

    @staticmethod
    def ensure_can_edit_profile(actor: ActorContext, target_user_id: str) -> None:
        """Проверяет право редактировать профиль."""

        if UserRole.ADMIN in actor.roles:
            return
        if actor.actor_id != target_user_id:
            raise AccessDeniedError("Можно редактировать только собственный профиль.")
