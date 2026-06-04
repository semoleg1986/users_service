from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from src.application.staff_invites.commands.dto import (
    ConsumeStaffInviteCommand,
    CreateStaffInviteCommand,
)
from src.application.staff_invites.handlers.manage_staff_invites_handler import (
    ConsumeStaffInviteHandler,
    CreateStaffInviteHandler,
)
from src.domain.errors import InvariantViolationError
from src.domain.shared.statuses import UserRole
from src.domain.users.profile.entity import UserProfile
from src.domain.users.profile.value_objects import DisplayName, Email
from src.infrastructure.db.inmemory.repositories import (
    InMemoryParentStudentLinkRepository,
    InMemoryStaffInviteRepository,
    InMemoryStudentInviteRepository,
    InMemoryUserProfileRepository,
)
from src.infrastructure.db.inmemory.uow import (
    InMemoryRepositoryProvider,
    InMemoryUnitOfWork,
)


@dataclass
class _Clock:
    now_value: datetime

    def now(self) -> datetime:
        return self.now_value


class _Ids:
    def __init__(self) -> None:
        self._n = 0

    def new(self) -> str:
        self._n += 1
        return f"staff-invite-{self._n}"


def _uow() -> tuple[InMemoryUnitOfWork, _Clock]:
    now = datetime(2026, 6, 4, 12, 0, tzinfo=UTC)
    clock = _Clock(now)
    uow = InMemoryUnitOfWork(
        InMemoryRepositoryProvider(
            user_profiles=InMemoryUserProfileRepository(),
            parent_student_links=InMemoryParentStudentLinkRepository(),
            student_invites=InMemoryStudentInviteRepository(),
            staff_invites=InMemoryStaffInviteRepository(),
        )
    )
    teacher = UserProfile.create(
        user_id="teacher-1",
        email=Email("teacher@example.com"),
        display_name=DisplayName("Teacher"),
        phone=None,
        initial_roles={UserRole.TEACHER},
        now=now,
        actor_id="system",
    )
    student = UserProfile.create(
        user_id="student-1",
        email=Email("student@example.com"),
        display_name=DisplayName("Student"),
        phone=None,
        initial_roles={UserRole.STUDENT},
        now=now,
        actor_id="system",
    )
    uow.repositories.user_profiles.save(teacher)
    uow.repositories.user_profiles.save(student)
    return uow, clock


def test_admin_can_create_and_consume_staff_invite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    uow, clock = _uow()
    token_urlsafe_path = (
        "src.application.staff_invites.handlers.manage_staff_invites_handler."
        "secrets.token_urlsafe"
    )
    monkeypatch.setattr(
        token_urlsafe_path,
        lambda _: "raw-staff-invite-token",
    )
    create = CreateStaffInviteHandler(
        uow_factory=lambda: uow,
        clock=clock,
        id_generator=_Ids(),
    )
    consume = ConsumeStaffInviteHandler(uow_factory=lambda: uow, clock=clock)

    created = create(
        CreateStaffInviteCommand(
            target_user_id="teacher-1",
            actor_id="admin-1",
            actor_roles=["admin"],
            ttl_seconds=3600,
            idempotency_key="staff-1",
        )
    )

    assert created.invite_id == "staff-invite-1"
    assert created.roles == ["teacher"]
    assert created.invite_token == "raw-staff-invite-token"

    consumed = consume(
        ConsumeStaffInviteCommand(
            token="raw-staff-invite-token", consumer="auth_service"
        )
    )
    assert consumed.invite_type == "staff"
    assert consumed.user_id == "teacher-1"
    assert consumed.roles == ["teacher"]


def test_staff_invite_rejects_student_profile() -> None:
    uow, clock = _uow()
    create = CreateStaffInviteHandler(
        uow_factory=lambda: uow,
        clock=clock,
        id_generator=_Ids(),
    )

    with pytest.raises(InvariantViolationError):
        create(
            CreateStaffInviteCommand(
                target_user_id="student-1",
                actor_id="admin-1",
                actor_roles=["admin"],
            )
        )
