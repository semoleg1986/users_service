"""Схемы users API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CreateUserRequest(BaseModel):
    """Request создания пользователя."""

    user_id: str | None = None
    email: str
    display_name: str = Field(min_length=1, max_length=120)
    phone: str | None = None
    roles: list[str] = Field(min_length=1)


class UpdateUserRequest(BaseModel):
    """Request обновления профиля пользователя."""

    display_name: str | None = None
    email: str | None = None
    phone: str | None = None


class CreateMyStudentRequest(BaseModel):
    """Request создания student profile текущим parent."""

    email: str
    display_name: str = Field(min_length=1, max_length=120)
    phone: str | None = None


class CreateStudentInviteRequest(BaseModel):
    """Request создания invite для student profile."""

    ttl_seconds: int = Field(default=86400, ge=60, le=604800)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=128)


class CreateStaffInviteRequest(BaseModel):
    """Request создания invite для studio/admin profile."""

    ttl_seconds: int = Field(default=86400, ge=60, le=604800)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=128)
    roles: list[str] | None = None


class EnsureMyProfileRequest(BaseModel):
    """Request bootstrap профиля текущего пользователя."""

    email: str
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = None


class AssignRoleRequest(BaseModel):
    """Request назначения роли."""

    role: str


class UserResponse(BaseModel):
    """Response профиля пользователя."""

    user_id: str
    email: str
    display_name: str
    phone: str | None = None
    status: str
    roles: list[str]
    created_at: datetime
    updated_at: datetime
    version: int


class StudentInviteResponse(BaseModel):
    """Response student invite."""

    invite_id: str
    parent_user_id: str
    student_user_id: str
    email: str
    status: str
    expires_at: datetime
    used_at: datetime | None = None
    revoked_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    version: int
    invite_token: str | None = None


class StaffInviteResponse(BaseModel):
    """Response staff invite."""

    invite_id: str
    creator_user_id: str
    target_user_id: str
    email: str
    roles: list[str]
    status: str
    expires_at: datetime
    used_at: datetime | None = None
    revoked_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    version: int
    invite_token: str | None = None


class UserListResponse(BaseModel):
    """Response списка пользователей."""

    items: list[UserResponse]


class PaginatedUserListResponse(BaseModel):
    """Response списка пользователей с пагинацией."""

    items: list[UserResponse]
    limit: int
    offset: int
    sort: str
