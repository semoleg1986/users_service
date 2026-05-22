"""Репозиторный порт агрегата StudentInvite."""

from __future__ import annotations

from typing import Protocol

from src.domain.links.student_invite.entity import StudentInvite


class StudentInviteRepository(Protocol):
    """Контракт репозитория student invites."""

    def get(self, invite_id: str) -> StudentInvite | None:
        """Возвращает invite по ID."""

    def get_by_parent_and_idempotency(
        self, *, parent_id: str, idempotency_key: str
    ) -> StudentInvite | None:
        """Возвращает invite по parent + idempotency key."""

    def get_pending_by_student(self, student_id: str) -> StudentInvite | None:
        """Возвращает pending invite для student, если есть."""

    def get_by_token_hash(self, token_hash: str) -> StudentInvite | None:
        """Возвращает invite по token hash."""

    def save(self, invite: StudentInvite) -> None:
        """Сохраняет invite."""
