from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from src.application.links.commands.dto import CreateParentStudentLinkCommand
from src.application.links.handlers.create_parent_student_link_handler import (
    CreateParentStudentLinkHandler,
)
from src.application.users.commands.dto import CreateUserProfileCommand
from src.application.users.handlers.create_user_profile_handler import CreateUserProfileHandler
from src.domain.errors import AccessDeniedError, InvariantViolationError
from src.infrastructure.db.inmemory.repositories import (
    InMemoryParentStudentLinkRepository,
    InMemoryUserProfileRepository,
)
from src.infrastructure.db.inmemory.uow import InMemoryRepositoryProvider, InMemoryUnitOfWork


@dataclass
class FakeClock:
    now_value: datetime

    def now(self) -> datetime:
        return self.now_value


class FakeIdGenerator:
    def __init__(self) -> None:
        self._n = 0

    def new(self) -> str:
        self._n += 1
        return f"id-{self._n}"


def _build_uow() -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork(
        InMemoryRepositoryProvider(
            user_profiles=InMemoryUserProfileRepository(),
            parent_student_links=InMemoryParentStudentLinkRepository(),
        )
    )


def test_create_user_profile_handler_creates_profile() -> None:
    uow = _build_uow()
    handler = CreateUserProfileHandler(
        uow=uow,
        clock=FakeClock(datetime(2026, 4, 6, tzinfo=UTC)),
        id_generator=FakeIdGenerator(),
    )
    result = handler(
        CreateUserProfileCommand(
            user_id=None,
            email="parent@example.com",
            display_name="Parent User",
            phone="+995555111222",
            roles=["parent"],
            actor_id="admin-1",
        )
    )

    assert result.user_id == "id-1"
    assert result.status == "active"
    assert result.roles == ["parent"]


def test_create_user_profile_handler_rejects_duplicate_email() -> None:
    uow = _build_uow()
    handler = CreateUserProfileHandler(
        uow=uow,
        clock=FakeClock(datetime(2026, 4, 6, tzinfo=UTC)),
        id_generator=FakeIdGenerator(),
    )
    cmd = CreateUserProfileCommand(
        user_id=None,
        email="user@example.com",
        display_name="User 1",
        phone=None,
        roles=["student"],
        actor_id="admin-1",
    )
    handler(cmd)
    with pytest.raises(InvariantViolationError):
        handler(cmd)


def test_create_parent_student_link_handler_creates_active_link() -> None:
    uow = _build_uow()
    clock = FakeClock(datetime(2026, 4, 6, tzinfo=UTC))
    id_generator = FakeIdGenerator()

    create_user = CreateUserProfileHandler(uow=uow, clock=clock, id_generator=id_generator)
    create_link = CreateParentStudentLinkHandler(
        uow=uow,
        clock=clock,
        id_generator=id_generator,
    )

    parent = create_user(
        CreateUserProfileCommand(
            user_id="parent-1",
            email="parent1@example.com",
            display_name="Parent 1",
            phone=None,
            roles=["parent"],
            actor_id="admin-1",
        )
    )
    student = create_user(
        CreateUserProfileCommand(
            user_id="student-1",
            email="student1@example.com",
            display_name="Student 1",
            phone=None,
            roles=["student"],
            actor_id="admin-1",
        )
    )
    result = create_link(
        CreateParentStudentLinkCommand(
            link_id=None,
            parent_id=parent.user_id,
            student_id=student.user_id,
            actor_id=parent.user_id,
            actor_roles=["parent"],
            note="my child",
        )
    )

    assert result.status == "active"
    assert result.parent_id == "parent-1"
    assert result.student_id == "student-1"


def test_create_parent_student_link_handler_checks_policy() -> None:
    uow = _build_uow()
    clock = FakeClock(datetime(2026, 4, 6, tzinfo=UTC))
    id_generator = FakeIdGenerator()

    create_user = CreateUserProfileHandler(uow=uow, clock=clock, id_generator=id_generator)
    create_link = CreateParentStudentLinkHandler(
        uow=uow,
        clock=clock,
        id_generator=id_generator,
    )

    create_user(
        CreateUserProfileCommand(
            user_id="parent-1",
            email="parent1@example.com",
            display_name="Parent 1",
            phone=None,
            roles=["parent"],
            actor_id="admin-1",
        )
    )
    create_user(
        CreateUserProfileCommand(
            user_id="student-1",
            email="student1@example.com",
            display_name="Student 1",
            phone=None,
            roles=["student"],
            actor_id="admin-1",
        )
    )

    with pytest.raises(AccessDeniedError):
        create_link(
            CreateParentStudentLinkCommand(
                link_id=None,
                parent_id="parent-1",
                student_id="student-1",
                actor_id="teacher-1",
                actor_roles=["teacher"],
            )
        )

