"""Схемы internal API users_service."""

from __future__ import annotations

from pydantic import BaseModel


class TeacherInfoResponse(BaseModel):
    """Response профиля преподавателя для межсервисного вызова."""

    teacher_id: str
    display_name: str
    status: str
    roles: list[str]
