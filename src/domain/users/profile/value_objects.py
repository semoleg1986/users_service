"""Value Objects агрегата UserProfile."""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.domain.errors import InvariantViolationError

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_PATTERN = re.compile(r"^\+?[0-9]{7,15}$")


@dataclass(frozen=True, slots=True)
class DisplayName:
    """
    Отображаемое имя пользователя.

    :param value: Значение имени.
    :type value: str
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise InvariantViolationError("Отображаемое имя не может быть пустым.")
        if len(self.value.strip()) > 120:
            raise InvariantViolationError("Отображаемое имя слишком длинное.")


@dataclass(frozen=True, slots=True)
class Email:
    """
    Email пользователя.

    :param value: Значение email.
    :type value: str
    """

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not _EMAIL_PATTERN.fullmatch(normalized):
            raise InvariantViolationError("Некорректный формат email.")
        object.__setattr__(self, "value", normalized)


@dataclass(frozen=True, slots=True)
class Phone:
    """
    Телефон пользователя.

    :param value: Значение телефона в международном формате.
    :type value: str
    """

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not _PHONE_PATTERN.fullmatch(normalized):
            raise InvariantViolationError("Некорректный формат телефона.")
        object.__setattr__(self, "value", normalized)
