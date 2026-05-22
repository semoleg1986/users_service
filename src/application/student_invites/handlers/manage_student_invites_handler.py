"""Handlers создания/consume student invite."""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from src.application.common.dto import ConsumedStudentInviteResult, StudentInviteResult
from src.application.common.mappers import to_student_invite_result
from src.application.ports.clock import Clock
from src.application.ports.id_generator import IdGenerator
from src.application.ports.unit_of_work import UnitOfWorkFactory
from src.application.student_invites.commands.dto import (
    ConsumeStudentInviteCommand,
    CreateStudentInviteCommand,
)
from src.domain.errors import AccessDeniedError, InvariantViolationError
from src.domain.links.parent_student_link.policies import ParentStudentLinkPolicy
from src.domain.links.student_invite.entity import StudentInvite
from src.domain.links.student_invite.value_objects import (
    InviteIdempotencyKey,
    InviteTokenHash,
)
from src.domain.shared.statuses import InviteStatus, UserRole
from src.domain.users.profile.policies import ActorContext


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class CreateStudentInviteHandler:
    """Создает student invite для parent-managed child."""

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

    def __call__(self, command: CreateStudentInviteCommand) -> StudentInviteResult:
        if command.ttl_seconds <= 0:
            raise InvariantViolationError("ttl_seconds должен быть больше нуля.")

        actor = ActorContext.from_claims(command.actor_id, command.actor_roles)
        ParentStudentLinkPolicy.ensure_can_create_link(
            actor, parent_id=command.actor_id
        )

        with self._uow_factory() as uow:
            parent_profile = uow.repositories.user_profiles.get(command.actor_id)
            if parent_profile is None:
                raise InvariantViolationError("Parent профиль не найден.")

            student = uow.repositories.user_profiles.get(command.student_id)
            if student is None:
                raise InvariantViolationError("Student профиль не найден.")

            student_roles = {role.value for role in student.roles}
            if UserRole.STUDENT.value not in student_roles:
                raise InvariantViolationError(
                    "Invite можно создать только для student профиля."
                )

            link = uow.repositories.parent_student_links.get_active_by_pair(
                command.actor_id, command.student_id
            )
            if link is None:
                raise AccessDeniedError("student_id не связан с текущим parent.")

            idempotency_key = (
                InviteIdempotencyKey(command.idempotency_key)
                if command.idempotency_key is not None
                else None
            )
            if idempotency_key is not None:
                existing = (
                    uow.repositories.student_invites.get_by_parent_and_idempotency(
                        parent_id=command.actor_id,
                        idempotency_key=idempotency_key.value,
                    )
                )
                if existing is not None:
                    return to_student_invite_result(existing)

            active = uow.repositories.student_invites.get_pending_by_student(
                command.student_id
            )
            if active is not None:
                active.mark_expired_if_needed(
                    now=self._clock.now(), actor_id=command.actor_id
                )
                if active.status == InviteStatus.PENDING:
                    raise InvariantViolationError(
                        "Для этого student уже существует активный invite."
                    )
                uow.repositories.student_invites.save(active)

            now = self._clock.now()
            raw_token = secrets.token_urlsafe(48)
            invite = StudentInvite.create(
                invite_id=self._id_generator.new(),
                parent_user_id=command.actor_id,
                student_user_id=command.student_id,
                email=student.email.value,
                token_hash=InviteTokenHash(_hash_token(raw_token)),
                expires_at=now + timedelta(seconds=command.ttl_seconds),
                now=now,
                actor_id=command.actor_id,
                idempotency_key=idempotency_key,
            )
            uow.repositories.student_invites.save(invite)
            uow.commit()
            return to_student_invite_result(invite, invite_token=raw_token)


class ConsumeStudentInviteHandler:
    """Consume use-case для auth_service."""

    def __init__(self, *, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def __call__(
        self, command: ConsumeStudentInviteCommand
    ) -> ConsumedStudentInviteResult:
        token = command.token.strip()
        if not token:
            raise InvariantViolationError("token не может быть пустым.")

        with self._uow_factory() as uow:
            invite = uow.repositories.student_invites.get_by_token_hash(
                _hash_token(token)
            )
            if invite is None:
                raise InvariantViolationError("invite не найден.")

            now = self._clock.now()
            invite.consume(now=now, actor_id=command.consumer)
            uow.repositories.student_invites.save(invite)
            uow.commit()

            return ConsumedStudentInviteResult(
                invite_id=invite.invite_id,
                parent_user_id=invite.parent_user_id,
                student_user_id=invite.student_user_id,
                email=invite.email,
                consumed_at=invite.used_at or now,
            )
