from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from src.application.facade.application_facade import ApplicationFacade
from src.application.users.commands.dto import (
    AssignRoleCommand,
    ChangeUserStatusCommand,
    RevokeRoleCommand,
    UpdateUserProfileCommand,
)
from src.application.users.handlers.manage_user_handlers import (
    AssignRoleHandler,
    ChangeUserStatusHandler,
    RevokeRoleHandler,
    UpdateUserProfileHandler,
)
from src.domain.errors import InvariantViolationError
from src.domain.shared.statuses import UserRole
from src.domain.users.profile.entity import UserProfile
from src.domain.users.profile.value_objects import DisplayName, Email
from src.infrastructure.db.inmemory.repositories import (
    InMemoryParentStudentLinkRepository,
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


def _uow() -> tuple[InMemoryUnitOfWork, _Clock]:
    now = datetime(2026, 4, 9, tzinfo=UTC)
    clock = _Clock(now)
    uow = InMemoryUnitOfWork(
        InMemoryRepositoryProvider(
            user_profiles=InMemoryUserProfileRepository(),
            parent_student_links=InMemoryParentStudentLinkRepository(),
        )
    )
    admin = UserProfile.create(
        user_id="admin-1",
        email=Email("admin@example.com"),
        display_name=DisplayName("Admin"),
        phone=None,
        initial_roles={UserRole.ADMIN},
        now=now,
        actor_id="system",
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
    uow.repositories.user_profiles.save(admin)
    uow.repositories.user_profiles.save(parent)
    return uow, clock


def test_application_facade_missing_handlers() -> None:
    facade = ApplicationFacade()

    class C:
        pass

    class Q:
        pass

    with pytest.raises(LookupError):
        facade.execute(C())
    with pytest.raises(LookupError):
        facade.query(Q())


def test_manage_handlers_missing_and_status_branches() -> None:
    uow, clock = _uow()

    update = UpdateUserProfileHandler(uow_factory=lambda: uow, clock=clock)
    assign = AssignRoleHandler(uow_factory=lambda: uow, clock=clock)
    revoke = RevokeRoleHandler(uow_factory=lambda: uow, clock=clock)
    status = ChangeUserStatusHandler(uow_factory=lambda: uow, clock=clock)

    with pytest.raises(InvariantViolationError):
        update(
            UpdateUserProfileCommand(
                user_id="missing",
                actor_id="admin-1",
                actor_roles=["admin"],
            )
        )

    # email change + phone branch (empty -> None)
    updated = update(
        UpdateUserProfileCommand(
            user_id="parent-1",
            actor_id="admin-1",
            actor_roles=["admin"],
            email="newparent@example.com",
            phone="",
        )
    )
    assert updated.email == "newparent@example.com"

    with pytest.raises(InvariantViolationError):
        assign(
            AssignRoleCommand(
                user_id="missing",
                role="student",
                actor_id="admin-1",
                actor_roles=["admin"],
            )
        )

    with pytest.raises(InvariantViolationError):
        revoke(
            RevokeRoleCommand(
                user_id="missing",
                role="student",
                actor_id="admin-1",
                actor_roles=["admin"],
            )
        )

    archived = status(
        ChangeUserStatusCommand(
            user_id="parent-1",
            action="archive",
            actor_id="admin-1",
            actor_roles=["admin"],
        )
    )
    assert archived.status == "archived"

    restored = status(
        ChangeUserStatusCommand(
            user_id="parent-1",
            action="restore",
            actor_id="admin-1",
            actor_roles=["admin"],
        )
    )
    assert restored.status == "active"
