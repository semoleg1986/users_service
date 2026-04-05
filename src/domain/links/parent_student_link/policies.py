"""Доменные политики доступа links/parent_student_link."""

from __future__ import annotations

from src.domain.errors import AccessDeniedError
from src.domain.shared.statuses import UserRole
from src.domain.users.profile.policies import ActorContext


class ParentStudentLinkPolicy:
    """Политики операций со связями parent-student."""

    @staticmethod
    def ensure_can_create_link(actor: ActorContext, parent_id: str) -> None:
        """Проверяет право создать связь parent-student."""

        if UserRole.ADMIN in actor.roles:
            return
        if UserRole.PARENT not in actor.roles:
            raise AccessDeniedError("Только parent или admin может создать связь.")
        if actor.actor_id != parent_id:
            raise AccessDeniedError("Parent может создавать связь только для себя.")

    @staticmethod
    def ensure_can_remove_link(actor: ActorContext, parent_id: str) -> None:
        """Проверяет право удалить связь parent-student."""

        if UserRole.ADMIN in actor.roles:
            return
        if actor.actor_id != parent_id:
            raise AccessDeniedError("Удалять связь может только владелец-parent или admin.")

