"""Query DTO student invites."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetStudentInviteByIdQuery:
    """Возвращает invite по ID."""

    invite_id: str
    actor_id: str
    actor_roles: list[str]
