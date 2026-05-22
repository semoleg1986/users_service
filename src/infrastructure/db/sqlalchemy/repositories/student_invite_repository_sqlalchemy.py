"""SQLAlchemy репозиторий StudentInvite."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.links.student_invite.entity import StudentInvite
from src.domain.links.student_invite.value_objects import (
    InviteIdempotencyKey,
    InviteTokenHash,
)
from src.domain.shared.entity import EntityMeta
from src.domain.shared.statuses import InviteStatus
from src.infrastructure.db.sqlalchemy.models import StudentInviteModel


class SqlAlchemyStudentInviteRepository:
    """Репозиторий StudentInvite на SQLAlchemy."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, invite_id: str) -> StudentInvite | None:
        model = self._db.get(StudentInviteModel, invite_id)
        if model is None:
            return None
        return self._to_entity(model)

    def get_by_parent_and_idempotency(
        self, *, parent_id: str, idempotency_key: str
    ) -> StudentInvite | None:
        row = self._db.execute(
            select(StudentInviteModel).where(
                StudentInviteModel.parent_user_id == parent_id,
                StudentInviteModel.idempotency_key == idempotency_key,
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        return self._to_entity(row)

    def get_pending_by_student(self, student_id: str) -> StudentInvite | None:
        row = self._db.execute(
            select(StudentInviteModel).where(
                StudentInviteModel.student_user_id == student_id,
                StudentInviteModel.status == InviteStatus.PENDING.value,
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        return self._to_entity(row)

    def get_by_token_hash(self, token_hash: str) -> StudentInvite | None:
        row = self._db.execute(
            select(StudentInviteModel).where(
                StudentInviteModel.token_hash == token_hash
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        return self._to_entity(row)

    def save(self, invite: StudentInvite) -> None:
        model = self._db.get(StudentInviteModel, invite.invite_id)
        if model is None:
            model = StudentInviteModel(invite_id=invite.invite_id)
            self._db.add(model)

        model.parent_user_id = invite.parent_user_id
        model.student_user_id = invite.student_user_id
        model.email = invite.email
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
    def _to_entity(model: StudentInviteModel) -> StudentInvite:
        return StudentInvite(
            invite_id=model.invite_id,
            parent_user_id=model.parent_user_id,
            student_user_id=model.student_user_id,
            email=model.email,
            token_hash=InviteTokenHash(model.token_hash),
            status=InviteStatus(model.status),
            expires_at=model.expires_at,
            used_at=model.used_at,
            revoked_at=model.revoked_at,
            idempotency_key=(
                InviteIdempotencyKey(model.idempotency_key)
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
