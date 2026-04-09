from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from src.application.users.commands.dto import (
    AssignRoleCommand,
    ChangeUserStatusCommand,
    RevokeRoleCommand,
    UpdateUserProfileCommand,
)
from src.application.users.handlers.get_user_handlers import (
    GetMyProfileHandler,
    ListParentStudentsHandler,
)
from src.application.users.handlers.manage_user_handlers import (
    AssignRoleHandler,
    ChangeUserStatusHandler,
    RevokeRoleHandler,
    UpdateUserProfileHandler,
)
from src.application.users.queries.dto import GetMyProfileQuery, ListParentStudentsQuery
from src.domain.errors import AccessDeniedError, InvariantViolationError
from src.domain.links.parent_student_link.entity import ParentStudentLink
from src.domain.shared.statuses import UserRole
from src.domain.users.profile.entity import UserProfile
from src.domain.users.profile.value_objects import DisplayName, Email
from src.infrastructure.db.inmemory.repositories import (
    InMemoryParentStudentLinkRepository,
    InMemoryUserProfileRepository,
)
from src.infrastructure.db.inmemory.uow import InMemoryRepositoryProvider, InMemoryUnitOfWork


@dataclass
class _Clock:
    now_value: datetime

    def now(self) -> datetime:
        return self.now_value


def _uow_with_profiles() -> tuple[InMemoryUnitOfWork, _Clock]:
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
    student = UserProfile.create(
        user_id="student-1",
        email=Email("student@example.com"),
        display_name=DisplayName("Student"),
        phone=None,
        initial_roles={UserRole.STUDENT},
        now=now,
        actor_id="system",
    )
    uow.repositories.user_profiles.save(admin)
    uow.repositories.user_profiles.save(parent)
    uow.repositories.user_profiles.save(student)
    return uow, clock


def test_update_profile_self_service_and_duplicate_email_branch() -> None:
    uow, clock = _uow_with_profiles()
    handler = UpdateUserProfileHandler(uow=uow, clock=clock)

    result = handler(
        UpdateUserProfileCommand(
            user_id="parent-1",
            actor_id="parent-1",
            actor_roles=["parent"],
            display_name="Parent New",
        )
    )
    assert result.display_name == "Parent New"

    with pytest.raises(InvariantViolationError):
        handler(
            UpdateUserProfileCommand(
                user_id="parent-1",
                actor_id="admin-1",
                actor_roles=["admin"],
                email="student@example.com",
            )
        )


def test_assign_and_revoke_role_handlers_with_last_admin_guard() -> None:
    uow, clock = _uow_with_profiles()
    assign = AssignRoleHandler(uow=uow, clock=clock)
    revoke = RevokeRoleHandler(uow=uow, clock=clock)

    assigned = assign(
        AssignRoleCommand(
            user_id="student-1",
            role="teacher",
            actor_id="admin-1",
            actor_roles=["admin"],
        )
    )
    assert "teacher" in assigned.roles

    with pytest.raises(InvariantViolationError):
        revoke(
            RevokeRoleCommand(
                user_id="admin-1",
                role="admin",
                actor_id="admin-1",
                actor_roles=["admin"],
            )
        )


def test_change_status_handler_unknown_action_and_not_found() -> None:
    uow, clock = _uow_with_profiles()
    handler = ChangeUserStatusHandler(uow=uow, clock=clock)

    with pytest.raises(InvariantViolationError):
        handler(
            ChangeUserStatusCommand(
                user_id="missing",
                action="block",
                actor_id="admin-1",
                actor_roles=["admin"],
            )
        )

    with pytest.raises(InvariantViolationError):
        handler(
            ChangeUserStatusCommand(
                user_id="student-1",
                action="unknown",
                actor_id="admin-1",
                actor_roles=["admin"],
            )
        )


def test_get_my_profile_and_parent_students_branches() -> None:
    uow, clock = _uow_with_profiles()
    del clock

    get_me = GetMyProfileHandler(uow=uow)
    with pytest.raises(InvariantViolationError):
        get_me(GetMyProfileQuery(actor_id="missing", actor_roles=["parent"]))

    link = ParentStudentLink.request(
        link_id="l-1",
        parent_id="parent-1",
        student_id="student-1",
        now=datetime(2026, 4, 9, tzinfo=UTC),
        actor_id="parent-1",
    )
    link.activate(now=datetime(2026, 4, 9, tzinfo=UTC), actor_id="admin-1")
    uow.repositories.parent_student_links.save(link)

    list_handler = ListParentStudentsHandler(uow=uow)
    items = list_handler(ListParentStudentsQuery(actor_id="parent-1", actor_roles=["parent"]))
    assert len(items) == 1

    with pytest.raises(AccessDeniedError):
        list_handler(ListParentStudentsQuery(actor_id="teacher-1", actor_roles=["teacher"]))
