"""Агрегат UserProfile."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.domain.errors import InvariantViolationError
from src.domain.shared.entity import EntityMeta
from src.domain.shared.statuses import UserRole, UserStatus

from .value_objects import DisplayName, Email, Phone


@dataclass(slots=True)
class RoleAssignment:
    """
    Сущность назначения роли пользователя.

    :param role: Роль.
    :type role: UserRole
    """

    role: UserRole
    assigned_at: datetime
    assigned_by: str
    revoked_at: datetime | None = None
    revoked_by: str | None = None

    @property
    def is_active(self) -> bool:
        """Признак активного назначения роли."""

        return self.revoked_at is None

    def revoke(self, *, at: datetime, actor_id: str) -> None:
        """Отзывает назначение роли."""

        self.revoked_at = at
        self.revoked_by = actor_id


@dataclass(slots=True)
class UserProfile:
    """
    Aggregate Root профиля пользователя.

    :param user_id: Уникальный ID пользователя.
    :type user_id: str
    """

    user_id: str
    email: Email
    display_name: DisplayName
    phone: Phone | None
    status: UserStatus
    meta: EntityMeta
    role_assignments: dict[UserRole, RoleAssignment] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        email: Email,
        display_name: DisplayName,
        phone: Phone | None,
        initial_roles: set[UserRole],
        now: datetime,
        actor_id: str,
    ) -> "UserProfile":
        """Создает новый профиль пользователя."""

        if not initial_roles:
            raise InvariantViolationError(
                "У пользователя должна быть хотя бы одна роль."
            )
        profile = cls(
            user_id=user_id,
            email=email,
            display_name=display_name,
            phone=phone,
            status=UserStatus.ACTIVE,
            meta=EntityMeta.create(at=now, actor_id=actor_id),
        )
        for role in initial_roles:
            profile.role_assignments[role] = RoleAssignment(
                role=role,
                assigned_at=now,
                assigned_by=actor_id,
            )
        return profile

    @property
    def roles(self) -> set[UserRole]:
        """Возвращает множество активных ролей."""

        return {
            role
            for role, assignment in self.role_assignments.items()
            if assignment.is_active
        }

    def change_display_name(
        self, *, display_name: DisplayName, now: datetime, actor_id: str
    ) -> None:
        """Обновляет отображаемое имя."""

        self._ensure_not_archived()
        self.display_name = display_name
        self.meta.touch(at=now, actor_id=actor_id)

    def change_email(self, *, email: Email, now: datetime, actor_id: str) -> None:
        """Обновляет email пользователя."""

        self._ensure_not_archived()
        self.email = email
        self.meta.touch(at=now, actor_id=actor_id)

    def change_phone(
        self, *, phone: Phone | None, now: datetime, actor_id: str
    ) -> None:
        """Обновляет телефон профиля."""

        self._ensure_not_archived()
        self.phone = phone
        self.meta.touch(at=now, actor_id=actor_id)

    def assign_role(self, *, role: UserRole, now: datetime, actor_id: str) -> None:
        """Назначает роль пользователю."""

        self._ensure_not_archived()
        assignment = self.role_assignments.get(role)
        if assignment is not None and assignment.is_active:
            return
        self.role_assignments[role] = RoleAssignment(
            role=role,
            assigned_at=now,
            assigned_by=actor_id,
        )
        self.meta.touch(at=now, actor_id=actor_id)

    def revoke_role(self, *, role: UserRole, now: datetime, actor_id: str) -> None:
        """Отзывает назначенную роль пользователя."""

        self._ensure_not_archived()
        assignment = self.role_assignments.get(role)
        if assignment is None or not assignment.is_active:
            return
        if len(self.roles) <= 1:
            raise InvariantViolationError(
                "Нельзя отозвать последнюю активную роль пользователя."
            )
        assignment.revoke(at=now, actor_id=actor_id)
        self.meta.touch(at=now, actor_id=actor_id)

    def block(self, *, now: datetime, actor_id: str) -> None:
        """Блокирует пользователя."""

        if self.status == UserStatus.ARCHIVED:
            raise InvariantViolationError("Нельзя блокировать архивного пользователя.")
        self.status = UserStatus.BLOCKED
        self.meta.touch(at=now, actor_id=actor_id)

    def activate(self, *, now: datetime, actor_id: str) -> None:
        """Активирует пользователя."""

        if self.status == UserStatus.ARCHIVED:
            raise InvariantViolationError("Нельзя активировать архивного пользователя.")
        self.status = UserStatus.ACTIVE
        self.meta.touch(at=now, actor_id=actor_id)

    def archive(self, *, now: datetime, actor_id: str) -> None:
        """Архивирует пользователя."""

        self.status = UserStatus.ARCHIVED
        self.meta.mark_archived(at=now, actor_id=actor_id)

    def restore(self, *, now: datetime, actor_id: str) -> None:
        """Восстанавливает архивированного пользователя в active."""

        if self.status != UserStatus.ARCHIVED:
            raise InvariantViolationError(
                "Восстановление возможно только для архивного пользователя."
            )
        self.status = UserStatus.ACTIVE
        self.meta.touch(at=now, actor_id=actor_id)

    def _ensure_not_archived(self) -> None:
        if self.status == UserStatus.ARCHIVED:
            raise InvariantViolationError(
                "Операция недоступна для архивного пользователя."
            )
