"""Схемы links API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CreateParentStudentLinkRequest(BaseModel):
    """Request создания связи parent-student."""

    link_id: str | None = None
    parent_id: str
    student_id: str
    note: str | None = None


class ParentStudentLinkResponse(BaseModel):
    """Response связи parent-student."""

    link_id: str
    parent_id: str
    student_id: str
    status: str
    note: str | None
    created_at: datetime
    updated_at: datetime
    version: int


class ParentStudentLinkListResponse(BaseModel):
    """Response списка связей parent-student."""

    items: list[ParentStudentLinkResponse]
