"""Value Objects агрегата ParentStudentLink."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.errors import InvariantViolationError


@dataclass(frozen=True, slots=True)
class LinkNote:
    """
    Комментарий к связи parent-student.

    :param value: Текст примечания.
    :type value: str
    """

    value: str

    def __post_init__(self) -> None:
        if len(self.value) > 500:
            raise InvariantViolationError("Комментарий к связи слишком длинный.")
