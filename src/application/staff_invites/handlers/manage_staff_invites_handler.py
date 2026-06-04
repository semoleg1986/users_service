"""Handlers создания/consume staff invite."""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from src.application.common.dto import ConsumedInviteResult, StaffInviteResult
from src.application.common.mappers import to_staff_invite_result
from src.application.ports.clock import Clock
from src.application.ports.id_generator import IdGenerator
from src.application.ports.unit_of_work import UnitOfWorkFactory
from src.application.staff_invites.commands.dto import (
    ConsumeStaffInviteCommand,
    CreateStaffInviteCommand,
)
from src.domain.errors import InvariantViolationError
from src.domain.links.staff_invite.entity import STAFF_INVITE_ROLES, StaffInvite
from src.domain.links.staff_invite.value_objects import (
    StaffInviteIdempotencyKey,
    StaffInviteTokenHash,
)
from src.domain.shared.statuses import InviteStatus, UserRole, UserStatus
from src.domain.users.profile.policies import ActorContext, AdminPolicy


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class CreateStaffInviteHandler:
    """Создает staff invite для Studio/admin identity onboarding."""

    def __init__(
        self,
        *,
        uow_factory: UnitOfWorkFactory,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._id_generator = id_generator

    def __call__(self, command: CreateStaffInviteCommand) -> StaffInviteResult:
        if command.ttl_seconds <= 0:
            raise InvariantViolationError("ttl_seconds должен быть больше нуля.")

        actor = ActorContext.from_claims(command.actor_id, command.actor_roles)
        AdminPolicy.ensure_can_manage_users(actor)

        requested_roles = (
            {UserRole(role) for role in command.roles}
            if command.roles is not None
            else None
        )
        if requested_roles is not None and not requested_roles:
            raise InvariantViolationError("roles не может быть пустым.")
        if requested_roles is not None and not requested_roles.issubset(
            STAFF_INVITE_ROLES
        ):
            raise InvariantViolationError(
                "staff invite поддерживает только studio/admin роли."
            )

        with self._uow_factory() as uow:
            target = uow.repositories.user_profiles.get(command.target_user_id)
            if target is None:
                raise InvariantViolationError("Пользователь не найден.")
            if target.status != UserStatus.ACTIVE:
                raise InvariantViolationError(
                    "Invite доступен только для active пользователя."
                )

            target_staff_roles = target.roles.intersection(STAFF_INVITE_ROLES)
            roles = requested_roles or target_staff_roles
            if not roles:
                raise InvariantViolationError(
                    "Staff invite можно создать только для "
                    "admin/teacher/content_manager профиля."
                )
            if not roles.issubset(target_staff_roles):
                raise InvariantViolationError(
                    "Invite roles должны быть активными ролями target profile."
                )

            idempotency_key = (
                StaffInviteIdempotencyKey(command.idempotency_key)
                if command.idempotency_key is not None
                else None
            )
            if idempotency_key is not None:
                existing = (
                    uow.repositories.staff_invites.get_by_creator_and_idempotency(
                        creator_id=command.actor_id,
                        idempotency_key=idempotency_key.value,
                    )
                )
                if existing is not None:
                    return to_staff_invite_result(existing)

            active = uow.repositories.staff_invites.get_pending_by_target(
                command.target_user_id
            )
            if active is not None:
                active.mark_expired_if_needed(
                    now=self._clock.now(), actor_id=command.actor_id
                )
                if active.status == InviteStatus.PENDING:
                    raise InvariantViolationError(
                        "Для этого staff пользователя уже существует активный invite."
                    )
                uow.repositories.staff_invites.save(active)

            now = self._clock.now()
            raw_token = secrets.token_urlsafe(48)
            invite = StaffInvite.create(
                invite_id=self._id_generator.new(),
                creator_user_id=command.actor_id,
                target_user_id=command.target_user_id,
                email=target.email.value,
                roles=roles,
                token_hash=StaffInviteTokenHash(_hash_token(raw_token)),
                expires_at=now + timedelta(seconds=command.ttl_seconds),
                now=now,
                actor_id=command.actor_id,
                idempotency_key=idempotency_key,
            )
            uow.repositories.staff_invites.save(invite)
            uow.commit()
            return to_staff_invite_result(invite, invite_token=raw_token)


class ConsumeStaffInviteHandler:
    """Consume use-case для auth_service."""

    def __init__(self, *, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def __call__(self, command: ConsumeStaffInviteCommand) -> ConsumedInviteResult:
        token = command.token.strip()
        if not token:
            raise InvariantViolationError("token не может быть пустым.")

        with self._uow_factory() as uow:
            invite = uow.repositories.staff_invites.get_by_token_hash(
                _hash_token(token)
            )
            if invite is None:
                raise InvariantViolationError("invite не найден.")

            now = self._clock.now()
            invite.consume(now=now, actor_id=command.consumer)
            uow.repositories.staff_invites.save(invite)
            uow.commit()

            return ConsumedInviteResult(
                invite_id=invite.invite_id,
                invite_type="staff",
                user_id=invite.target_user_id,
                email=invite.email,
                roles=sorted(role.value for role in invite.roles),
                consumed_at=invite.used_at or now,
            )
