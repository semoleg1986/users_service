"""HTTP роуты internal v1."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, Header, HTTPException

from src.application.links.queries.dto import ListParentStudentLinksQuery
from src.application.student_invites.commands.dto import ConsumeStudentInviteCommand
from src.application.users.queries.dto import GetUserByIdQuery
from src.domain.errors import InvariantViolationError
from src.interface.http.observability import increment_counter
from src.interface.http.v1.schemas.internal import (
    ConsumedStudentInviteResponse,
    ConsumeStudentInviteRequest,
    ParentStudentRelationResponse,
    StudentParentsResponse,
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


@router.get(
    "/students/{student_id}/parents",
    response_model=StudentParentsResponse,
)
def list_student_parents(
    student_id: str,
    service_token: str | None = Header(default=None, alias="X-Service-Token"),
    expected_token: str = Depends(get_service_token),
    facade=Depends(get_facade),
) -> StudentParentsResponse:
    """Возвращает активные parent ids для межсервисной интеграции."""

    if not service_token:
        raise HTTPException(status_code=401, detail="Требуется X-Service-Token.")
    if service_token != expected_token:
        raise HTTPException(status_code=401, detail="Некорректный X-Service-Token.")

    links = facade.query(
        ListParentStudentLinksQuery(
            actor_id="internal-users-service",
            actor_roles=["admin"],
            student_id=student_id,
        )
    )
    parent_ids = sorted({item.parent_id for item in links if item.status == "active"})
    return StudentParentsResponse(student_id=student_id, parent_ids=parent_ids)


@router.post(
    "/student-invites/consume",
    response_model=ConsumedStudentInviteResponse,
)
def consume_student_invite(
    payload: ConsumeStudentInviteRequest,
    service_token: str | None = Header(default=None, alias="X-Service-Token"),
    expected_token: str = Depends(get_service_token),
    facade=Depends(get_facade),
) -> ConsumedStudentInviteResponse:
    """Одноразово consume invite token для auth onboarding flow."""

    if not service_token:
        raise HTTPException(status_code=401, detail="Требуется X-Service-Token.")
    if service_token != expected_token:
        raise HTTPException(status_code=401, detail="Некорректный X-Service-Token.")

    result = facade.execute(
        ConsumeStudentInviteCommand(
            token=payload.token,
            consumer=payload.consumer,
        )
    )
    increment_counter(
        "student_invites_consumed_total",
        "Total consumed student invites by internal consumers.",
        result="success",
        consumer=payload.consumer,
    )
    return ConsumedStudentInviteResponse(**asdict(result))
