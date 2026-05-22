"""Агрегат StudentInvite."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.errors import InvariantViolationError
from src.domain.links.student_invite.value_objects import (
    InviteIdempotencyKey,
    InviteTokenHash,
)
from src.domain.shared.entity import EntityMeta
from src.domain.shared.statuses import InviteStatus


@dataclass(slots=True)
class StudentInvite:
    """Одноразовый invite для привязки auth identity к existing student profile."""

    invite_id: str
    parent_user_id: str
    student_user_id: str
    email: str
    token_hash: InviteTokenHash
    status: InviteStatus
    expires_at: datetime
    meta: EntityMeta
    used_at: datetime | None = None
    revoked_at: datetime | None = None
    idempotency_key: InviteIdempotencyKey | None = None

    @classmethod
    def create(
        cls,
        *,
        invite_id: str,
        parent_user_id: str,
        student_user_id: str,
        email: str,
        token_hash: InviteTokenHash,
        expires_at: datetime,
        now: datetime,
        actor_id: str,
        idempotency_key: InviteIdempotencyKey | None = None,
    ) -> "StudentInvite":
        """Создает новый pending invite."""

        if expires_at <= now:
            raise InvariantViolationError("expires_at должен быть в будущем.")

        return cls(
            invite_id=invite_id,
            parent_user_id=parent_user_id,
            student_user_id=student_user_id,
            email=email.strip().lower(),
            token_hash=token_hash,
            status=InviteStatus.PENDING,
            expires_at=expires_at,
            meta=EntityMeta.create(at=now, actor_id=actor_id),
            idempotency_key=idempotency_key,
        )

    def mark_expired_if_needed(self, *, now: datetime, actor_id: str) -> None:
        """Переводит invite в expired, если TTL истек."""

        if self.status != InviteStatus.PENDING:
            return
        if self.expires_at > now:
            return

        self.status = InviteStatus.EXPIRED
        self.meta.touch(at=now, actor_id=actor_id)

    def consume(self, *, now: datetime, actor_id: str) -> None:
        """Помечает invite как использованный."""

        self.mark_expired_if_needed(now=now, actor_id=actor_id)

        if self.status == InviteStatus.USED:
            raise InvariantViolationError("invite уже использован.")
        if self.status == InviteStatus.REVOKED:
            raise InvariantViolationError("invite отозван.")
        if self.status == InviteStatus.EXPIRED:
            raise InvariantViolationError("invite истек.")
        if self.status != InviteStatus.PENDING:
            raise InvariantViolationError("invite недоступен для использования.")

        self.status = InviteStatus.USED
        self.used_at = now
        self.meta.touch(at=now, actor_id=actor_id)

    def revoke(self, *, now: datetime, actor_id: str) -> None:
        """Отзывает pending invite."""

        self.mark_expired_if_needed(now=now, actor_id=actor_id)

        if self.status == InviteStatus.USED:
            raise InvariantViolationError("Использованный invite нельзя отозвать.")
        if self.status == InviteStatus.EXPIRED:
            raise InvariantViolationError("Истекший invite нельзя отозвать.")
        if self.status == InviteStatus.REVOKED:
            return

        self.status = InviteStatus.REVOKED
        self.revoked_at = now
        self.meta.touch(at=now, actor_id=actor_id)
