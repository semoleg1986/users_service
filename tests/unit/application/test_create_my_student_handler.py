from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from src.application.users.commands.dto import CreateMyStudentCommand
from src.application.users.handlers.create_my_student_handler import (
    CreateMyStudentHandler,
)
from src.domain.errors import AccessDeniedError, InvariantViolationError
from src.domain.shared.statuses import UserRole
from src.domain.users.profile.entity import UserProfile
from src.domain.users.profile.value_objects import DisplayName, Email
from src.infrastructure.db.inmemory.repositories import (
    InMemoryParentStudentLinkRepository,
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
        self._values = iter(["student-new-1", "link-new-1"])

    def new(self) -> str:
        return next(self._values)


def _uow_with_parent() -> tuple[InMemoryUnitOfWork, _Clock]:
    now = datetime(2026, 4, 9, tzinfo=UTC)
    clock = _Clock(now)
    uow = InMemoryUnitOfWork(
        InMemoryRepositoryProvider(
            user_profiles=InMemoryUserProfileRepository(),
            parent_student_links=InMemoryParentStudentLinkRepository(),
            student_invites=InMemoryStudentInviteRepository(),
        )
    )
    parent = UserProfile.create(
        user_id="parent-1",
        email=Email("parent@example.com"),
        display_name=DisplayName("Parent"),
        phone=None,
        initial_roles={UserRole.PARENT},
        now=now,
        actor_id="system",
    )
    uow.repositories.user_profiles.save(parent)
    return uow, clock


def test_parent_can_create_student_and_link() -> None:
    uow, clock = _uow_with_parent()
    handler = CreateMyStudentHandler(
        uow_factory=lambda: uow,
        clock=clock,
        id_generator=_Ids(),
    )

    result = handler(
        CreateMyStudentCommand(
            email="student-new@example.com",
            display_name="Student New",
            phone=None,
            actor_id="parent-1",
            actor_roles=["parent"],
        )
    )

    assert result.user_id == "student-new-1"
    assert result.roles == ["student"]
    links = uow.repositories.parent_student_links.list(parent_id="parent-1")
    assert len(links) == 1
    assert links[0].student_id == "student-new-1"


def test_non_parent_cannot_create_student() -> None:
    uow, clock = _uow_with_parent()
    handler = CreateMyStudentHandler(
        uow_factory=lambda: uow,
        clock=clock,
        id_generator=_Ids(),
    )

    with pytest.raises(AccessDeniedError):
        handler(
            CreateMyStudentCommand(
                email="student-new@example.com",
                display_name="Student New",
                phone=None,
                actor_id="teacher-1",
                actor_roles=["teacher"],
            )
        )


def test_duplicate_email_is_rejected() -> None:
    uow, clock = _uow_with_parent()
    existing_student = UserProfile.create(
        user_id="student-dup",
        email=Email("student-dup@example.com"),
        display_name=DisplayName("Student Dup"),
        phone=None,
        initial_roles={UserRole.STUDENT},
        now=clock.now(),
        actor_id="system",
    )
    uow.repositories.user_profiles.save(existing_student)
    handler = CreateMyStudentHandler(
        uow_factory=lambda: uow,
        clock=clock,
        id_generator=_Ids(),
    )

    with pytest.raises(InvariantViolationError):
        handler(
            CreateMyStudentCommand(
                email="student-dup@example.com",
                display_name="Student New",
                phone=None,
                actor_id="parent-1",
                actor_roles=["parent"],
            )
        )


def test_inactive_parent_is_rejected_by_domain_policy() -> None:
    uow, clock = _uow_with_parent()
    parent = uow.repositories.user_profiles.get("parent-1")
    assert parent is not None
    parent.block(now=clock.now(), actor_id="admin-1")
    uow.repositories.user_profiles.save(parent)

    handler = CreateMyStudentHandler(
        uow_factory=lambda: uow,
        clock=clock,
        id_generator=_Ids(),
    )

    with pytest.raises(InvariantViolationError):
        handler(
            CreateMyStudentCommand(
                email="student-new@example.com",
                display_name="Student New",
                phone=None,
                actor_id="parent-1",
                actor_roles=["parent"],
            )
        )
