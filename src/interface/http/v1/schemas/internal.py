"""Схемы internal API users_service."""

from __future__ import annotations

from datetime import datetime

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


class ConsumeStudentInviteRequest(BaseModel):
    """Request consume student invite token для internal вызова auth_service."""

    token: str
    consumer: str = "auth_service"


class ConsumedStudentInviteResponse(BaseModel):
    """Response consumed student invite."""

    invite_id: str
    parent_user_id: str
    student_user_id: str
    email: str
    consumed_at: datetime
