"""Ошибки доменного слоя users_service."""


class DomainError(Exception):
    """Базовая ошибка доменного слоя."""


class InvariantViolationError(DomainError):
    """Ошибка нарушения доменного инварианта."""


class AccessDeniedError(DomainError):
    """Ошибка доступа по доменным политикам."""
