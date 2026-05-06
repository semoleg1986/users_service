from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.application.links.commands.dto import (
    CreateParentStudentLinkCommand,
    RemoveParentStudentLinkCommand,
)
from src.application.links.handlers.create_parent_student_link_handler import (
    CreateParentStudentLinkHandler,
    RemoveParentStudentLinkHandler,
)
from src.application.users.commands.dto import CreateUserProfileCommand
from src.application.users.handlers.create_user_profile_handler import (
    CreateUserProfileHandler,
)
from src.application.users.handlers.get_user_handlers import GetUserByIdHandler
from src.application.users.queries.dto import GetUserByIdQuery
from src.domain.errors import AccessDeniedError, InvariantViolationError
from src.infrastructure.db.inmemory.repositories import (
    InMemoryParentStudentLinkRepository,
    InMemoryUserProfileRepository,
)
from src.infrastructure.db.inmemory.uow import (
    InMemoryRepositoryProvider,
    InMemoryUnitOfWork,
)


class _Clock:
    def now(self) -> datetime:
        return datetime(2026, 4, 9, tzinfo=UTC)


class _Ids:
    def __init__(self) -> None:
        self._n = 0

    def new(self) -> str:
        self._n += 1
        return f"id-{self._n}"


def _ctx() -> tuple[InMemoryUnitOfWork, _Clock, _Ids]:
    uow = InMemoryUnitOfWork(
        InMemoryRepositoryProvider(
            user_profiles=InMemoryUserProfileRepository(),
            parent_student_links=InMemoryParentStudentLinkRepository(),
        )
    )
    return uow, _Clock(), _Ids()


def test_get_user_by_id_requires_admin_and_not_found() -> None:
    uow, _, _ = _ctx()
    handler = GetUserByIdHandler(uow_factory=lambda: uow)

    with pytest.raises(AccessDeniedError):
        handler(
            GetUserByIdQuery(user_id="u-1", actor_id="u-1", actor_roles=["student"])
        )

    with pytest.raises(InvariantViolationError):
        handler(
            GetUserByIdQuery(user_id="u-1", actor_id="admin-1", actor_roles=["admin"])
        )


def test_link_handlers_duplicate_and_remove_missing() -> None:
    uow, clock, ids = _ctx()
    create_user = CreateUserProfileHandler(
        uow_factory=lambda: uow, clock=clock, id_generator=ids
    )

    create_user(
        CreateUserProfileCommand(
            user_id="admin-1",
            email="admin@example.com",
            display_name="Admin",
            phone=None,
            roles=["admin"],
            actor_id="admin-1",
        )
    )
    create_user(
        CreateUserProfileCommand(
            user_id="parent-1",
            email="parent@example.com",
            display_name="Parent",
            phone=None,
            roles=["parent"],
            actor_id="admin-1",
        )
    )
    create_user(
        CreateUserProfileCommand(
            user_id="student-1",
            email="student@example.com",
            display_name="Student",
            phone=None,
            roles=["student"],
            actor_id="admin-1",
        )
    )

    create_link = CreateParentStudentLinkHandler(
        uow_factory=lambda: uow, clock=clock, id_generator=ids
    )
    create_link(
        CreateParentStudentLinkCommand(
            link_id="link-1",
            parent_id="parent-1",
            student_id="student-1",
            actor_id="admin-1",
            actor_roles=["admin"],
        )
    )

    with pytest.raises(InvariantViolationError):
        create_link(
            CreateParentStudentLinkCommand(
                link_id="link-2",
                parent_id="parent-1",
                student_id="student-1",
                actor_id="admin-1",
                actor_roles=["admin"],
            )
        )

    remove = RemoveParentStudentLinkHandler(uow_factory=lambda: uow, clock=clock)
    with pytest.raises(InvariantViolationError):
        remove(
            RemoveParentStudentLinkCommand(
                link_id="missing",
                actor_id="admin-1",
                actor_roles=["admin"],
            )
        )
