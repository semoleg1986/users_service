from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from src.application.users.commands.dto import EnsureMyProfileCommand
from src.application.users.handlers.ensure_my_profile_handler import (
    EnsureMyProfileHandler,
)
from src.domain.errors import InvariantViolationError
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


def _uow() -> tuple[InMemoryUnitOfWork, _Clock]:
    now = datetime(2026, 4, 9, tzinfo=UTC)
    clock = _Clock(now)
    uow = InMemoryUnitOfWork(
        InMemoryRepositoryProvider(
            user_profiles=InMemoryUserProfileRepository(),
            parent_student_links=InMemoryParentStudentLinkRepository(),
            student_invites=InMemoryStudentInviteRepository(),
        )
    )
    return uow, clock


def test_ensure_my_profile_creates_profile() -> None:
    uow, clock = _uow()
    handler = EnsureMyProfileHandler(uow_factory=lambda: uow, clock=clock)

    result = handler(
        EnsureMyProfileCommand(
            actor_id="parent-1",
            actor_roles=["parent"],
            email="parent@example.com",
            display_name="Parent One",
            phone=None,
        )
    )

    assert result.user_id == "parent-1"
    assert result.roles == ["parent"]


def test_ensure_my_profile_is_idempotent() -> None:
    uow, clock = _uow()
    existing = UserProfile.create(
        user_id="parent-1",
        email=Email("parent@example.com"),
        display_name=DisplayName("Parent One"),
        phone=None,
        initial_roles={UserRole.PARENT},
        now=clock.now(),
        actor_id="system",
    )
    uow.repositories.user_profiles.save(existing)
    handler = EnsureMyProfileHandler(uow_factory=lambda: uow, clock=clock)

    result = handler(
        EnsureMyProfileCommand(
            actor_id="parent-1",
            actor_roles=["parent"],
            email="parent@example.com",
            display_name="Parent One",
            phone=None,
        )
    )

    assert result.user_id == "parent-1"
    assert result.email == "parent@example.com"


def test_ensure_my_profile_rejects_duplicate_email_for_other_user() -> None:
    uow, clock = _uow()
    existing = UserProfile.create(
        user_id="other-user",
        email=Email("parent@example.com"),
        display_name=DisplayName("Other Parent"),
        phone=None,
        initial_roles={UserRole.PARENT},
        now=clock.now(),
        actor_id="system",
    )
    uow.repositories.user_profiles.save(existing)
    handler = EnsureMyProfileHandler(uow_factory=lambda: uow, clock=clock)

    with pytest.raises(InvariantViolationError):
        handler(
            EnsureMyProfileCommand(
                actor_id="parent-1",
                actor_roles=["parent"],
                email="parent@example.com",
                display_name="Parent One",
                phone=None,
            )
        )
