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


class UserListResponse(BaseModel):
    """Response списка пользователей."""

    items: list[UserResponse]


class PaginatedUserListResponse(BaseModel):
    """Response списка пользователей с пагинацией."""

    items: list[UserResponse]
    limit: int
    offset: int
    sort: str
