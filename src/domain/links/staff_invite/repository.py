"""Репозиторный порт StaffInvite."""

from __future__ import annotations

from typing import Protocol

from src.domain.links.staff_invite.entity import StaffInvite


class StaffInviteRepository(Protocol):
    """Контракт репозитория staff invites."""

    def get(self, invite_id: str) -> StaffInvite | None:
        """Возвращает invite по ID."""

    def get_by_creator_and_idempotency(
        self, *, creator_id: str, idempotency_key: str
    ) -> StaffInvite | None:
        """Возвращает invite по creator + idempotency key."""

    def get_pending_by_target(self, target_user_id: str) -> StaffInvite | None:
        """Возвращает pending invite для staff target, если есть."""

    def get_by_token_hash(self, token_hash: str) -> StaffInvite | None:
        """Возвращает invite по token hash."""

    def save(self, invite: StaffInvite) -> None:
        """Сохраняет invite."""
