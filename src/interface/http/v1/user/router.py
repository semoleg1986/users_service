"""HTTP роуты user v1."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends

from src.application.users.commands.dto import (
    EnsureMyProfileCommand,
    UpdateUserProfileCommand,
)
from src.application.users.queries.dto import GetMyProfileQuery
from src.interface.http.common.actor import HttpActor, get_http_actor
from src.interface.http.v1.schemas.users import (
    EnsureMyProfileRequest,
    UpdateUserRequest,
    UserResponse,
)
from src.interface.http.wiring import get_facade

router = APIRouter(prefix="/v1/user", tags=["user"])


@router.post("/me", response_model=UserResponse)
def ensure_me(
    payload: EnsureMyProfileRequest,
    actor: HttpActor = Depends(get_http_actor),
    facade=Depends(get_facade),
) -> UserResponse:
    """Идемпотентно создает профиль текущего пользователя при первом входе."""

    result = facade.execute(
        EnsureMyProfileCommand(
            actor_id=actor.actor_id,
            actor_roles=actor.roles,
            email=payload.email,
            display_name=payload.display_name,
            phone=payload.phone,
        )
    )
    return UserResponse(**asdict(result))


@router.get("/me", response_model=UserResponse)
def get_me(
    actor: HttpActor = Depends(get_http_actor), facade=Depends(get_facade)
) -> UserResponse:
    """Возвращает профиль текущего пользователя."""

    result = facade.query(
        GetMyProfileQuery(actor_id=actor.actor_id, actor_roles=actor.roles)
    )
    return UserResponse(**asdict(result))


@router.patch("/me", response_model=UserResponse)
def update_me(
    payload: UpdateUserRequest,
    actor: HttpActor = Depends(get_http_actor),
    facade=Depends(get_facade),
) -> UserResponse:
    """Обновляет профиль текущего пользователя."""

    result = facade.execute(
        UpdateUserProfileCommand(
            user_id=actor.actor_id,
            actor_id=actor.actor_id,
            actor_roles=actor.roles,
            display_name=payload.display_name,
            email=payload.email,
            phone=payload.phone,
        )
    )
    return UserResponse(**asdict(result))
