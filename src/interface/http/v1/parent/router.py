"""HTTP роуты parent v1."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, Query

from src.application.users.queries.dto import ListParentStudentsQuery
from src.interface.http.common.actor import HttpActor, get_http_actor
from src.interface.http.observability import increment_counter
from src.interface.http.v1.schemas.users import PaginatedUserListResponse, UserResponse
from src.interface.http.wiring import get_facade

router = APIRouter(prefix="/v1/parent", tags=["parent"])


@router.get("/me/students", response_model=PaginatedUserListResponse)
def list_my_students(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="created_at:asc", pattern="^created_at:(asc|desc)$"),
    actor: HttpActor = Depends(get_http_actor),
    facade=Depends(get_facade),
) -> PaginatedUserListResponse:
    """Возвращает список учеников, связанных с текущим parent."""

    result = facade.query(
        ListParentStudentsQuery(
            actor_id=actor.actor_id,
            actor_roles=actor.roles,
            limit=limit,
            offset=offset,
            sort=sort,
        )
    )
    increment_counter(
        "parent_students_list_requests_total",
        "Total parent student list requests.",
        result="success",
        sort=sort,
    )
    return PaginatedUserListResponse(
        items=[UserResponse(**asdict(item)) for item in result],
        limit=limit,
        offset=offset,
        sort=sort,
    )
