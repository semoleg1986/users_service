"""Агрегат ParentStudentLink."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.errors import InvariantViolationError
from src.domain.shared.entity import EntityMeta
from src.domain.shared.statuses import LinkStatus
from .value_objects import LinkNote


@dataclass(slots=True)
class ParentStudentLink:
    """
    Aggregate Root связи parent-student.

    :param link_id: Уникальный идентификатор связи.
    :type link_id: str
    :param parent_id: Идентификатор пользователя-родителя.
    :type parent_id: str
    :param student_id: Идентификатор пользователя-ученика.
    :type student_id: str
    """

    link_id: str
    parent_id: str
    student_id: str
    status: LinkStatus
    meta: EntityMeta
    note: LinkNote | None = None

    @classmethod
    def request(
        cls,
        *,
        link_id: str,
        parent_id: str,
        student_id: str,
        now: datetime,
        actor_id: str,
        note: LinkNote | None = None,
    ) -> "ParentStudentLink":
        """Создает запрос на связь parent-student."""

        if parent_id == student_id:
            raise InvariantViolationError("Родитель и ученик не могут совпадать.")
        return cls(
            link_id=link_id,
            parent_id=parent_id,
            student_id=student_id,
            status=LinkStatus.REQUESTED,
            meta=EntityMeta.create(at=now, actor_id=actor_id),
            note=note,
        )

    def activate(self, *, now: datetime, actor_id: str) -> None:
        """Активирует связь parent-student."""

        if self.status == LinkStatus.REMOVED:
            raise InvariantViolationError("Удаленную связь нельзя активировать.")
        self.status = LinkStatus.ACTIVE
        self.meta.touch(at=now, actor_id=actor_id)

    def remove(self, *, now: datetime, actor_id: str) -> None:
        """Удаляет (деактивирует) связь parent-student."""

        if self.status == LinkStatus.REMOVED:
            return
        self.status = LinkStatus.REMOVED
        self.meta.touch(at=now, actor_id=actor_id)

