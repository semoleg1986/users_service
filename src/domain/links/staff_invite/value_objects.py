"""Value Objects staff invite."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.errors import InvariantViolationError


@dataclass(frozen=True, slots=True)
class StaffInviteTokenHash:
    """Хэш одноразового staff invite токена."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise InvariantViolationError("token_hash не может быть пустым.")


@dataclass(frozen=True, slots=True)
class StaffInviteIdempotencyKey:
    """Idempotency key при создании staff invite."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise InvariantViolationError("idempotency_key не может быть пустым.")
        object.__setattr__(self, "value", normalized)
