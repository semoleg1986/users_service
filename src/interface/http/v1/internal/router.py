"""HTTP роуты internal v1."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException

from src.application.links.queries.dto import ListParentStudentLinksQuery
from src.application.users.queries.dto import GetUserByIdQuery
from src.domain.errors import InvariantViolationError
from src.interface.http.observability import increment_counter
from src.interface.http.v1.schemas.internal import (
    ParentStudentRelationResponse,
    TeacherInfoResponse,
)
from src.interface.http.wiring import get_facade, get_service_token

router = APIRouter(prefix="/internal/v1", tags=["internal"])


@router.get("/teachers/{teacher_id}", response_model=TeacherInfoResponse)
def get_teacher_info(
    teacher_id: str,
    service_token: str | None = Header(default=None, alias="X-Service-Token"),
    expected_token: str = Depends(get_service_token),
    facade=Depends(get_facade),
) -> TeacherInfoResponse:
    """Возвращает профиль активного преподавателя для межсервисной интеграции."""

    if not service_token:
        raise HTTPException(status_code=401, detail="Требуется X-Service-Token.")
    if service_token != expected_token:
        raise HTTPException(status_code=401, detail="Некорректный X-Service-Token.")

    try:
        user = facade.query(
            GetUserByIdQuery(
                user_id=teacher_id,
                actor_id="internal-users-service",
                actor_roles=["admin"],
            )
        )
    except InvariantViolationError as exc:
        raise HTTPException(status_code=404, detail="Преподаватель не найден.") from exc

    normalized_roles = {role.strip().lower() for role in user.roles if role.strip()}
    if "teacher" not in normalized_roles or user.status != "active":
        raise HTTPException(
            status_code=404, detail="Преподаватель не найден или неактивен."
        )

    return TeacherInfoResponse(
        teacher_id=user.user_id,
        display_name=user.display_name,
        status=user.status,
        roles=user.roles,
    )


@router.get(
    "/parent-students/{parent_id}/{student_id}",
    response_model=ParentStudentRelationResponse,
)
def check_parent_student_relation(
    parent_id: str,
    student_id: str,
    service_token: str | None = Header(default=None, alias="X-Service-Token"),
    expected_token: str = Depends(get_service_token),
    facade=Depends(get_facade),
) -> ParentStudentRelationResponse:
    """Проверяет наличие активной связи parent-student для межсервисной интеграции."""

    if not service_token:
        raise HTTPException(status_code=401, detail="Требуется X-Service-Token.")
    if service_token != expected_token:
        raise HTTPException(status_code=401, detail="Некорректный X-Service-Token.")

    links = facade.query(
        ListParentStudentLinksQuery(
            actor_id="internal-users-service",
            actor_roles=["admin"],
            parent_id=parent_id,
            student_id=student_id,
        )
    )
    if not links:
        increment_counter(
            "internal_parent_student_lookup_failures_total",
            "Total internal parent-student lookup misses.",
            result="not_found",
        )
    return ParentStudentRelationResponse(
        parent_id=parent_id,
        student_id=student_id,
        has_relation=bool(links),
    )
