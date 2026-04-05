"""HTTP роуты parent v1."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends

from src.application.users.queries.dto import ListParentStudentsQuery
from src.interface.http.common.actor import HttpActor, get_http_actor
from src.interface.http.v1.schemas.users import UserListResponse, UserResponse
from src.interface.http.wiring import get_facade

router = APIRouter(prefix="/v1/parent", tags=["parent"])


@router.get("/me/students", response_model=UserListResponse)
def list_my_students(
    actor: HttpActor = Depends(get_http_actor),
    facade=Depends(get_facade),
) -> UserListResponse:
    """Возвращает список учеников, связанных с текущим parent."""

    result = facade.query(
        ListParentStudentsQuery(actor_id=actor.actor_id, actor_roles=actor.roles)
    )
    return UserListResponse(items=[UserResponse(**asdict(item)) for item in result])

