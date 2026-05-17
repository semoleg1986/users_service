"""Доменные политики создания student profile родителем."""

from __future__ import annotations

from src.domain.errors import InvariantViolationError
from src.domain.shared.statuses import UserRole, UserStatus
from src.domain.users.profile.entity import UserProfile


class ParentManagedStudentPolicy:
    """Политики parent-managed student enrollment."""

    @staticmethod
    def ensure_parent_can_create_student(parent_profile: UserProfile) -> None:
        """Проверяет, что профиль parent может создать student profile."""

        if UserRole.PARENT not in parent_profile.roles:
            raise InvariantViolationError(
                "Создавать ученика может только пользователь роли parent."
            )
        if parent_profile.status != UserStatus.ACTIVE:
            raise InvariantViolationError(
                "Создавать ученика можно только для parent в статусе active."
            )
