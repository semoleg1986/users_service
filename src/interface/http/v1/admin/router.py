"""HTTP роуты admin v1."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Body, Depends, Query

from src.application.links.commands.dto import (
    CreateParentStudentLinkCommand,
    RemoveParentStudentLinkCommand,
)
from src.application.links.queries.dto import ListParentStudentLinksQuery
from src.application.users.commands.dto import (
    AssignRoleCommand,
    ChangeUserStatusCommand,
    CreateUserProfileCommand,
    RevokeRoleCommand,
    UpdateUserProfileCommand,
)
from src.application.users.queries.dto import GetUserByIdQuery, ListUsersQuery
from src.interface.http.v1.schemas.links import (
    CreateParentStudentLinkRequest,
    ParentStudentLinkListResponse,
    ParentStudentLinkResponse,
    RemoveParentStudentLinkRequest,
)
from src.interface.http.v1.schemas.users import (
    AssignRoleRequest,
    CreateUserRequest,
    UpdateUserRequest,
    UserListResponse,
    UserResponse,
)
from src.interface.http.wiring import get_facade

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(payload: CreateUserRequest, facade=Depends(get_facade)) -> UserResponse:
    """Создает профиль пользователя."""

    result = facade.execute(
        CreateUserProfileCommand(
            user_id=payload.user_id,
            email=str(payload.email),
            display_name=payload.display_name,
            phone=payload.phone,
            roles=payload.roles,
            actor_id=payload.actor_id,
        )
    )
    return UserResponse(**asdict(result))


@router.post("/links", response_model=ParentStudentLinkResponse, status_code=201)
def create_parent_student_link(
    payload: CreateParentStudentLinkRequest, facade=Depends(get_facade)
) -> ParentStudentLinkResponse:
    """Создает связь родитель-ученик."""

    result = facade.execute(
        CreateParentStudentLinkCommand(
            link_id=payload.link_id,
            parent_id=payload.parent_id,
            student_id=payload.student_id,
            actor_id=payload.actor_id,
            actor_roles=payload.actor_roles,
            note=payload.note,
        )
    )
    return ParentStudentLinkResponse(**asdict(result))


@router.get("/users", response_model=UserListResponse)
def list_users(
    actor_id: str = Query(...),
    actor_roles: str = Query(...),
    role: str | None = Query(default=None),
    status: str | None = Query(default=None),
    facade=Depends(get_facade),
) -> UserListResponse:
    """Возвращает список пользователей."""

    result = facade.query(
        ListUsersQuery(
            actor_id=actor_id,
            actor_roles=[r.strip() for r in actor_roles.split(",") if r.strip()],
            role=role,
            status=status,
        )
    )
    return UserListResponse(items=[UserResponse(**asdict(item)) for item in result])


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    actor_id: str = Query(...),
    actor_roles: str = Query(...),
    facade=Depends(get_facade),
) -> UserResponse:
    """Возвращает пользователя по ID."""

    result = facade.query(
        GetUserByIdQuery(
            user_id=user_id,
            actor_id=actor_id,
            actor_roles=[r.strip() for r in actor_roles.split(",") if r.strip()],
        )
    )
    return UserResponse(**asdict(result))


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    payload: UpdateUserRequest,
    actor_id: str = Query(...),
    actor_roles: str = Query(...),
    facade=Depends(get_facade),
) -> UserResponse:
    """Обновляет профиль пользователя."""

    result = facade.execute(
        UpdateUserProfileCommand(
            user_id=user_id,
            actor_id=actor_id,
            actor_roles=[r.strip() for r in actor_roles.split(",") if r.strip()],
            display_name=payload.display_name,
            email=payload.email,
            phone=payload.phone,
        )
    )
    return UserResponse(**asdict(result))


@router.post("/users/{user_id}/roles", response_model=UserResponse)
def assign_role(user_id: str, payload: AssignRoleRequest, facade=Depends(get_facade)) -> UserResponse:
    """Назначает роль пользователю."""

    result = facade.execute(
        AssignRoleCommand(
            user_id=user_id,
            role=payload.role,
            actor_id=payload.actor_id,
            actor_roles=payload.actor_roles,
        )
    )
    return UserResponse(**asdict(result))


@router.delete("/users/{user_id}/roles", response_model=UserResponse)
def revoke_role(
    user_id: str,
    role: str = Query(...),
    actor_id: str = Query(...),
    actor_roles: str = Query(...),
    facade=Depends(get_facade),
) -> UserResponse:
    """Снимает роль у пользователя."""

    result = facade.execute(
        RevokeRoleCommand(
            user_id=user_id,
            role=role,
            actor_id=actor_id,
            actor_roles=[r.strip() for r in actor_roles.split(",") if r.strip()],
        )
    )
    return UserResponse(**asdict(result))


def _change_status(
    user_id: str,
    action: str,
    actor_id: str,
    actor_roles: list[str],
    facade,
) -> UserResponse:
    result = facade.execute(
        ChangeUserStatusCommand(
            user_id=user_id,
            action=action,
            actor_id=actor_id,
            actor_roles=actor_roles,
        )
    )
    return UserResponse(**asdict(result))


@router.post("/users/{user_id}/block", response_model=UserResponse)
def block_user(
    user_id: str,
    actor_id: str = Body(..., embed=True),
    actor_roles: list[str] = Body(..., embed=True),
    facade=Depends(get_facade),
) -> UserResponse:
    """Блокирует пользователя."""

    return _change_status(user_id, "block", actor_id, actor_roles, facade)


@router.post("/users/{user_id}/unblock", response_model=UserResponse)
def unblock_user(
    user_id: str,
    actor_id: str = Body(..., embed=True),
    actor_roles: list[str] = Body(..., embed=True),
    facade=Depends(get_facade),
) -> UserResponse:
    """Разблокирует пользователя."""

    return _change_status(user_id, "unblock", actor_id, actor_roles, facade)


@router.post("/users/{user_id}/archive", response_model=UserResponse)
def archive_user(
    user_id: str,
    actor_id: str = Body(..., embed=True),
    actor_roles: list[str] = Body(..., embed=True),
    facade=Depends(get_facade),
) -> UserResponse:
    """Архивирует пользователя."""

    return _change_status(user_id, "archive", actor_id, actor_roles, facade)


@router.post("/users/{user_id}/restore", response_model=UserResponse)
def restore_user(
    user_id: str,
    actor_id: str = Body(..., embed=True),
    actor_roles: list[str] = Body(..., embed=True),
    facade=Depends(get_facade),
) -> UserResponse:
    """Восстанавливает пользователя из архива."""

    return _change_status(user_id, "restore", actor_id, actor_roles, facade)


@router.get("/links", response_model=ParentStudentLinkListResponse)
def list_links(
    actor_id: str = Query(...),
    actor_roles: str = Query(...),
    parent_id: str | None = Query(default=None),
    student_id: str | None = Query(default=None),
    facade=Depends(get_facade),
) -> ParentStudentLinkListResponse:
    """Возвращает список связей родитель-ученик."""

    result = facade.query(
        ListParentStudentLinksQuery(
            actor_id=actor_id,
            actor_roles=[r.strip() for r in actor_roles.split(",") if r.strip()],
            parent_id=parent_id,
            student_id=student_id,
        )
    )
    return ParentStudentLinkListResponse(
        items=[ParentStudentLinkResponse(**asdict(item)) for item in result]
    )


@router.delete("/links/{link_id}", response_model=ParentStudentLinkResponse)
def remove_link(
    link_id: str,
    payload: RemoveParentStudentLinkRequest,
    facade=Depends(get_facade),
) -> ParentStudentLinkResponse:
    """Удаляет связь родитель-ученик."""

    result = facade.execute(
        RemoveParentStudentLinkCommand(
            link_id=link_id,
            actor_id=payload.actor_id,
            actor_roles=payload.actor_roles,
        )
    )
    return ParentStudentLinkResponse(**asdict(result))
