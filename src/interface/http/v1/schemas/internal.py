"""Схемы internal API users_service."""

from __future__ import annotations

from pydantic import BaseModel


class TeacherInfoResponse(BaseModel):
    """Response профиля преподавателя для межсервисного вызова."""

    teacher_id: str
    display_name: str
    status: str
    roles: list[str]


class ParentStudentRelationResponse(BaseModel):
    """Response проверки связи parent-student для межсервисного вызова."""

    parent_id: str
    student_id: str
    has_relation: bool


class StudentParentsResponse(BaseModel):
    """Response списка активных parent ids для student."""

    student_id: str
    parent_ids: list[str]
