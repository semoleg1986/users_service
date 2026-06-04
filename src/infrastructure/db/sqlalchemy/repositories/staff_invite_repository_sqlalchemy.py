"""SQLAlchemy репозиторий StaffInvite."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.links.staff_invite.entity import StaffInvite
from src.domain.links.staff_invite.value_objects import (
    StaffInviteIdempotencyKey,
    StaffInviteTokenHash,
)
from src.domain.shared.entity import EntityMeta
from src.domain.shared.statuses import InviteStatus, UserRole
from src.infrastructure.db.sqlalchemy.models import StaffInviteModel


class SqlAlchemyStaffInviteRepository:
    """Репозиторий StaffInvite на SQLAlchemy."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, invite_id: str) -> StaffInvite | None:
        model = self._db.get(StaffInviteModel, invite_id)
        if model is None:
            return None
        return self._to_entity(model)

    def get_by_creator_and_idempotency(
        self, *, creator_id: str, idempotency_key: str
    ) -> StaffInvite | None:
        row = self._db.execute(
            select(StaffInviteModel).where(
                StaffInviteModel.creator_user_id == creator_id,
                StaffInviteModel.idempotency_key == idempotency_key,
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        return self._to_entity(row)

    def get_pending_by_target(self, target_user_id: str) -> StaffInvite | None:
        row = self._db.execute(
            select(StaffInviteModel).where(
                StaffInviteModel.target_user_id == target_user_id,
                StaffInviteModel.status == InviteStatus.PENDING.value,
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        return self._to_entity(row)

    def get_by_token_hash(self, token_hash: str) -> StaffInvite | None:
        row = self._db.execute(
            select(StaffInviteModel).where(StaffInviteModel.token_hash == token_hash)
        ).scalar_one_or_none()
        if row is None:
            return None
        return self._to_entity(row)

    def save(self, invite: StaffInvite) -> None:
        model = self._db.get(StaffInviteModel, invite.invite_id)
        if model is None:
            model = StaffInviteModel(invite_id=invite.invite_id)
            self._db.add(model)

        model.creator_user_id = invite.creator_user_id
        model.target_user_id = invite.target_user_id
        model.email = invite.email
        model.roles_json = json.dumps(sorted(role.value for role in invite.roles))
        model.token_hash = invite.token_hash.value
        model.status = invite.status.value
        model.idempotency_key = (
            invite.idempotency_key.value if invite.idempotency_key is not None else None
        )
        model.expires_at = invite.expires_at
        model.used_at = invite.used_at
        model.revoked_at = invite.revoked_at
        model.version = invite.meta.version
        model.created_at = invite.meta.created_at
        model.created_by = invite.meta.created_by
        model.updated_at = invite.meta.updated_at
        model.updated_by = invite.meta.updated_by
        model.archived_at = invite.meta.archived_at
        model.archived_by = invite.meta.archived_by

    @staticmethod
    def _to_entity(model: StaffInviteModel) -> StaffInvite:
        roles = {UserRole(role) for role in json.loads(model.roles_json)}
        return StaffInvite(
            invite_id=model.invite_id,
            creator_user_id=model.creator_user_id,
            target_user_id=model.target_user_id,
            email=model.email,
            roles=roles,
            token_hash=StaffInviteTokenHash(model.token_hash),
            status=InviteStatus(model.status),
            expires_at=model.expires_at,
            used_at=model.used_at,
            revoked_at=model.revoked_at,
            idempotency_key=(
                StaffInviteIdempotencyKey(model.idempotency_key)
                if model.idempotency_key is not None
                else None
            ),
            meta=EntityMeta(
                version=model.version,
                created_at=model.created_at,
                created_by=model.created_by,
                updated_at=model.updated_at,
                updated_by=model.updated_by,
                archived_at=model.archived_at,
                archived_by=model.archived_by,
            ),
        )
