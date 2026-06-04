from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from src.application.student_invites.commands.dto import (
    ConsumeStudentInviteCommand,
    CreateStudentInviteCommand,
)
from src.application.student_invites.handlers.manage_student_invites_handler import (
    ConsumeStudentInviteHandler,
    CreateStudentInviteHandler,
)
from src.domain.errors import AccessDeniedError, InvariantViolationError
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
        return f"invite-{self._n}"


def _uow() -> tuple[InMemoryUnitOfWork, _Clock]:
    now = datetime(2026, 5, 22, 12, 0, tzinfo=UTC)
    clock = _Clock(now)
    uow = InMemoryUnitOfWork(
        InMemoryRepositoryProvider(
            user_profiles=InMemoryUserProfileRepository(),
            parent_student_links=InMemoryParentStudentLinkRepository(),
            student_invites=InMemoryStudentInviteRepository(),
            staff_invites=InMemoryStaffInviteRepository(),
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
    student = UserProfile.create(
        user_id="student-1",
        email=Email("student@example.com"),
        display_name=DisplayName("Student"),
        phone=None,
        initial_roles={UserRole.STUDENT},
        now=now,
        actor_id="system",
    )
    uow.repositories.user_profiles.save(parent)
    uow.repositories.user_profiles.save(student)

    link = uow.repositories.parent_student_links
    from src.domain.links.parent_student_link.entity import ParentStudentLink

    rel = ParentStudentLink.request(
        link_id="link-1",
        parent_id="parent-1",
        student_id="student-1",
        now=now,
        actor_id="system",
    )
    rel.activate(now=now, actor_id="system")
    link.save(rel)

    return uow, clock


def test_create_and_consume_student_invite(monkeypatch: pytest.MonkeyPatch) -> None:
    uow, clock = _uow()
    token_urlsafe_path = (
        "src.application.student_invites.handlers.manage_student_invites_handler."
        "secrets.token_urlsafe"
    )
    monkeypatch.setattr(
        token_urlsafe_path,
        lambda _: "raw-invite-token",
    )

    create = CreateStudentInviteHandler(
        uow_factory=lambda: uow,
        clock=clock,
        id_generator=_Ids(),
    )
    consume = ConsumeStudentInviteHandler(uow_factory=lambda: uow, clock=clock)

    created = create(
        CreateStudentInviteCommand(
            student_id="student-1",
            actor_id="parent-1",
            actor_roles=["parent"],
            ttl_seconds=3600,
            idempotency_key="idem-1",
        )
    )
    assert created.invite_id == "invite-1"
    assert created.status == "pending"
    assert created.invite_token == "raw-invite-token"

    consumed = consume(
        ConsumeStudentInviteCommand(token="raw-invite-token", consumer="auth_service")
    )
    assert consumed.student_user_id == "student-1"


def test_create_invite_requires_active_parent_student_link() -> None:
    uow, clock = _uow()
    # remove active relation
    for rel in uow.repositories.parent_student_links.list(parent_id="parent-1"):
        rel.remove(now=clock.now(), actor_id="parent-1")
        uow.repositories.parent_student_links.save(rel)

    create = CreateStudentInviteHandler(
        uow_factory=lambda: uow,
        clock=clock,
        id_generator=_Ids(),
    )

    with pytest.raises(AccessDeniedError):
        create(
            CreateStudentInviteCommand(
                student_id="student-1",
                actor_id="parent-1",
                actor_roles=["parent"],
            )
        )


def test_consume_invite_is_single_use(monkeypatch: pytest.MonkeyPatch) -> None:
    uow, clock = _uow()
    token_urlsafe_path = (
        "src.application.student_invites.handlers.manage_student_invites_handler."
        "secrets.token_urlsafe"
    )
    monkeypatch.setattr(
        token_urlsafe_path,
        lambda _: "raw-invite-token",
    )

    create = CreateStudentInviteHandler(
        uow_factory=lambda: uow,
        clock=clock,
        id_generator=_Ids(),
    )
    consume = ConsumeStudentInviteHandler(uow_factory=lambda: uow, clock=clock)

    created = create(
        CreateStudentInviteCommand(
            student_id="student-1",
            actor_id="parent-1",
            actor_roles=["parent"],
            ttl_seconds=3600,
        )
    )

    assert created.invite_token is not None
    consume(
        ConsumeStudentInviteCommand(token=created.invite_token, consumer="auth_service")
    )

    with pytest.raises(InvariantViolationError):
        consume(
            ConsumeStudentInviteCommand(
                token=created.invite_token, consumer="auth_service"
            )
        )


def test_create_invite_is_idempotent_by_key(monkeypatch: pytest.MonkeyPatch) -> None:
    uow, clock = _uow()
    token_urlsafe_path = (
        "src.application.student_invites.handlers.manage_student_invites_handler."
        "secrets.token_urlsafe"
    )
    monkeypatch.setattr(
        token_urlsafe_path,
        lambda _: "raw-invite-token",
    )

    create = CreateStudentInviteHandler(
        uow_factory=lambda: uow,
        clock=clock,
        id_generator=_Ids(),
    )

    first = create(
        CreateStudentInviteCommand(
            student_id="student-1",
            actor_id="parent-1",
            actor_roles=["parent"],
            idempotency_key="same-key",
        )
    )
    second = create(
        CreateStudentInviteCommand(
            student_id="student-1",
            actor_id="parent-1",
            actor_roles=["parent"],
            idempotency_key="same-key",
        )
    )

    assert first.invite_id == second.invite_id
    assert first.invite_token is not None
    assert second.invite_token is None
