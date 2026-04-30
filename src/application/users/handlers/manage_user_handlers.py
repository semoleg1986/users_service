"""Handlers управления профилем пользователя."""

from __future__ import annotations

from src.application.common.dto import UserProfileResult
from src.application.common.mappers import to_user_profile_result
from src.application.ports.clock import Clock
from src.application.ports.unit_of_work import UnitOfWork
from src.application.users.commands.dto import (
    AssignRoleCommand,
    ChangeUserStatusCommand,
    RevokeRoleCommand,
    UpdateUserProfileCommand,
)
from src.domain.errors import InvariantViolationError
from src.domain.shared.statuses import UserRole, UserStatus
from src.domain.users.profile.policies import (
    ActorContext,
    AdminPolicy,
    SelfServicePolicy,
)
from src.domain.users.profile.value_objects import DisplayName, Email, Phone


class UpdateUserProfileHandler:
    """Обновляет профиль пользователя."""

    def __init__(self, *, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    def __call__(self, command: UpdateUserProfileCommand) -> UserProfileResult:
        actor = ActorContext.from_claims(command.actor_id, command.actor_roles)
        if UserRole.ADMIN in actor.roles:
            AdminPolicy.ensure_can_manage_users(actor)
        else:
            SelfServicePolicy.ensure_can_edit_profile(
                actor, target_user_id=command.user_id
            )

        profile = self._uow.repositories.user_profiles.get(command.user_id)
        if profile is None:
            raise InvariantViolationError("Пользователь не найден.")
        now = self._clock.now()

        if command.email is not None and command.email != profile.email.value:
            existing = self._uow.repositories.user_profiles.get_by_email(command.email)
            if existing is not None and existing.user_id != profile.user_id:
                raise InvariantViolationError(
                    "Пользователь с таким email уже существует."
                )
            profile.change_email(
                email=Email(command.email), now=now, actor_id=command.actor_id
            )
        if command.display_name is not None:
            profile.change_display_name(
                display_name=DisplayName(command.display_name),
                now=now,
                actor_id=command.actor_id,
            )
        if command.phone is not None:
            phone = Phone(command.phone) if command.phone else None
            profile.change_phone(phone=phone, now=now, actor_id=command.actor_id)

        self._uow.repositories.user_profiles.save(profile)
        self._uow.commit()
        return to_user_profile_result(profile)


class AssignRoleHandler:
    """Назначает роль пользователю."""

    def __init__(self, *, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    def __call__(self, command: AssignRoleCommand) -> UserProfileResult:
        actor = ActorContext.from_claims(command.actor_id, command.actor_roles)
        AdminPolicy.ensure_can_manage_users(actor)
        profile = self._uow.repositories.user_profiles.get(command.user_id)
        if profile is None:
            raise InvariantViolationError("Пользователь не найден.")
        profile.assign_role(
            role=UserRole(command.role),
            now=self._clock.now(),
            actor_id=command.actor_id,
        )
        self._uow.repositories.user_profiles.save(profile)
        self._uow.commit()
        return to_user_profile_result(profile)


class RevokeRoleHandler:
    """Снимает роль у пользователя."""

    def __init__(self, *, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    def __call__(self, command: RevokeRoleCommand) -> UserProfileResult:
        actor = ActorContext.from_claims(command.actor_id, command.actor_roles)
        AdminPolicy.ensure_can_manage_users(actor)
        profile = self._uow.repositories.user_profiles.get(command.user_id)
        if profile is None:
            raise InvariantViolationError("Пользователь не найден.")
        role = UserRole(command.role)
        if role == UserRole.ADMIN and UserRole.ADMIN in profile.roles:
            active_admins = self._uow.repositories.user_profiles.list(
                role=UserRole.ADMIN.value,
                status=UserStatus.ACTIVE.value,
            )
            active_admin_ids = {item.user_id for item in active_admins}
            if active_admin_ids == {profile.user_id}:
                raise InvariantViolationError(
                    "Нельзя снять роль у последнего активного admin."
                )
        profile.revoke_role(
            role=role,
            now=self._clock.now(),
            actor_id=command.actor_id,
        )
        self._uow.repositories.user_profiles.save(profile)
        self._uow.commit()
        return to_user_profile_result(profile)


class ChangeUserStatusHandler:
    """Изменяет статус пользователя."""

    def __init__(self, *, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    def __call__(self, command: ChangeUserStatusCommand) -> UserProfileResult:
        actor = ActorContext.from_claims(command.actor_id, command.actor_roles)
        AdminPolicy.ensure_can_manage_users(actor)
        profile = self._uow.repositories.user_profiles.get(command.user_id)
        if profile is None:
            raise InvariantViolationError("Пользователь не найден.")
        if command.action in {"block", "archive"}:
            self._ensure_not_last_active_admin(profile)
        now = self._clock.now()
        if command.action == "block":
            profile.block(now=now, actor_id=command.actor_id)
        elif command.action == "unblock":
            profile.activate(now=now, actor_id=command.actor_id)
        elif command.action == "archive":
            profile.archive(now=now, actor_id=command.actor_id)
        elif command.action == "restore":
            profile.restore(now=now, actor_id=command.actor_id)
        else:
            raise InvariantViolationError("Неизвестное действие изменения статуса.")
        self._uow.repositories.user_profiles.save(profile)
        self._uow.commit()
        return to_user_profile_result(profile)

    def _ensure_not_last_active_admin(self, profile) -> None:
        if UserRole.ADMIN not in profile.roles:
            return
        if profile.status != UserStatus.ACTIVE:
            return
        active_admins = self._uow.repositories.user_profiles.list(
            role=UserRole.ADMIN.value,
            status=UserStatus.ACTIVE.value,
        )
        active_admin_ids = {item.user_id for item in active_admins}
        if active_admin_ids == {profile.user_id}:
            raise InvariantViolationError(
                "Нельзя деактивировать последнего активного admin."
            )
