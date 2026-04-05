"""SQLAlchemy репозиторий UserProfile."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.shared.entity import EntityMeta
from src.domain.shared.statuses import UserRole, UserStatus
from src.domain.users.profile.entity import RoleAssignment, UserProfile
from src.domain.users.profile.value_objects import DisplayName, Email, Phone
from src.infrastructure.db.sqlalchemy.models import UserProfileModel


class SqlAlchemyUserProfileRepository:
    """Репозиторий UserProfile на SQLAlchemy."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, user_id: str) -> UserProfile | None:
        model = self._db.get(UserProfileModel, user_id)
        if model is None:
            return None
        return self._to_entity(model)

    def get_by_email(self, email: str) -> UserProfile | None:
        row = self._db.execute(
            select(UserProfileModel).where(UserProfileModel.email == email.strip().lower())
        ).scalar_one_or_none()
        if row is None:
            return None
        return self._to_entity(row)

    def list(self, *, role: str | None = None, status: str | None = None) -> list[UserProfile]:
        stmt = select(UserProfileModel)
        rows = self._db.execute(stmt).scalars().all()
        items = [self._to_entity(row) for row in rows]
        if role is not None:
            items = [p for p in items if role in {r.value for r in p.roles}]
        if status is not None:
            items = [p for p in items if p.status.value == status]
        return sorted(items, key=lambda p: p.meta.created_at)

    def save(self, profile: UserProfile) -> None:
        model = self._db.get(UserProfileModel, profile.user_id)
        if model is None:
            model = UserProfileModel(user_id=profile.user_id)
            self._db.add(model)

        model.email = profile.email.value
        model.display_name = profile.display_name.value
        model.phone = profile.phone.value if profile.phone else None
        model.status = profile.status.value
        model.roles_json = json.dumps(sorted(role.value for role in profile.roles))
        model.version = profile.meta.version
        model.created_at = profile.meta.created_at
        model.created_by = profile.meta.created_by
        model.updated_at = profile.meta.updated_at
        model.updated_by = profile.meta.updated_by
        model.archived_at = profile.meta.archived_at
        model.archived_by = profile.meta.archived_by

    def _to_entity(self, model: UserProfileModel) -> UserProfile:
        meta = EntityMeta(
            version=model.version,
            created_at=model.created_at,
            created_by=model.created_by,
            updated_at=model.updated_at,
            updated_by=model.updated_by,
            archived_at=model.archived_at,
            archived_by=model.archived_by,
        )
        profile = UserProfile(
            user_id=model.user_id,
            email=Email(model.email),
            display_name=DisplayName(model.display_name),
            phone=Phone(model.phone) if model.phone else None,
            status=UserStatus(model.status),
            meta=meta,
            role_assignments={},
        )
        roles = json.loads(model.roles_json or "[]")
        for role_value in roles:
            role = UserRole(role_value)
            profile.role_assignments[role] = RoleAssignment(
                role=role,
                assigned_at=model.created_at,
                assigned_by=model.created_by,
                revoked_at=None,
                revoked_by=None,
            )
        return profile

