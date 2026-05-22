"""Статусы и ролевые enum users_service."""

from enum import StrEnum


class UserStatus(StrEnum):
    """Жизненный цикл пользователя."""

    ACTIVE = "active"
    BLOCKED = "blocked"
    ARCHIVED = "archived"


class LinkStatus(StrEnum):
    """Жизненный цикл связи родитель-ученик."""

    REQUESTED = "requested"
    ACTIVE = "active"
    REMOVED = "removed"


class UserRole(StrEnum):
    """Поддерживаемые роли пользователя."""

    ADMIN = "admin"
    TEACHER = "teacher"
    PARENT = "parent"
    STUDENT = "student"


class InviteStatus(StrEnum):
    """Жизненный цикл student invite."""

    PENDING = "pending"
    USED = "used"
    REVOKED = "revoked"
    EXPIRED = "expired"
