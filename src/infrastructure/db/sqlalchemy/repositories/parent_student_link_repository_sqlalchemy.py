"""SQLAlchemy репозиторий ParentStudentLink."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.links.parent_student_link.entity import ParentStudentLink
from src.domain.links.parent_student_link.value_objects import LinkNote
from src.domain.shared.entity import EntityMeta
from src.domain.shared.statuses import LinkStatus
from src.infrastructure.db.sqlalchemy.models import ParentStudentLinkModel


class SqlAlchemyParentStudentLinkRepository:
    """Репозиторий ParentStudentLink на SQLAlchemy."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, link_id: str) -> ParentStudentLink | None:
        model = self._db.get(ParentStudentLinkModel, link_id)
        if model is None:
            return None
        return self._to_entity(model)

    def get_active_by_pair(
        self, parent_id: str, student_id: str
    ) -> ParentStudentLink | None:
        row = self._db.execute(
            select(ParentStudentLinkModel).where(
                ParentStudentLinkModel.parent_id == parent_id,
                ParentStudentLinkModel.student_id == student_id,
                ParentStudentLinkModel.status == LinkStatus.ACTIVE.value,
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        return self._to_entity(row)

    def list(
        self, *, parent_id: str | None = None, student_id: str | None = None
    ) -> list[ParentStudentLink]:
        stmt = select(ParentStudentLinkModel)
        if parent_id is not None:
            stmt = stmt.where(ParentStudentLinkModel.parent_id == parent_id)
        if student_id is not None:
            stmt = stmt.where(ParentStudentLinkModel.student_id == student_id)
        rows = self._db.execute(stmt).scalars().all()
        return [self._to_entity(row) for row in rows]

    def list_active_by_parent(self, parent_id: str) -> list[ParentStudentLink]:
        rows = self._db.execute(
            select(ParentStudentLinkModel).where(
                ParentStudentLinkModel.parent_id == parent_id,
                ParentStudentLinkModel.status == LinkStatus.ACTIVE.value,
            )
        ).scalars()
        return [self._to_entity(row) for row in rows]

    def save(self, link: ParentStudentLink) -> None:
        model = self._db.get(ParentStudentLinkModel, link.link_id)
        if model is None:
            model = ParentStudentLinkModel(link_id=link.link_id)
            self._db.add(model)

        model.parent_id = link.parent_id
        model.student_id = link.student_id
        model.status = link.status.value
        model.note = link.note.value if link.note else None
        model.version = link.meta.version
        model.created_at = link.meta.created_at
        model.created_by = link.meta.created_by
        model.updated_at = link.meta.updated_at
        model.updated_by = link.meta.updated_by
        model.archived_at = link.meta.archived_at
        model.archived_by = link.meta.archived_by

    @staticmethod
    def _to_entity(model: ParentStudentLinkModel) -> ParentStudentLink:
        return ParentStudentLink(
            link_id=model.link_id,
            parent_id=model.parent_id,
            student_id=model.student_id,
            status=LinkStatus(model.status),
            meta=EntityMeta(
                version=model.version,
                created_at=model.created_at,
                created_by=model.created_by,
                updated_at=model.updated_at,
                updated_by=model.updated_by,
                archived_at=model.archived_at,
                archived_by=model.archived_by,
            ),
            note=LinkNote(model.note) if model.note else None,
        )
