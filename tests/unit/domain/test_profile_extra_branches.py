from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.domain.errors import AccessDeniedError, InvariantViolationError
from src.domain.links.parent_student_link.policies import ParentStudentLinkPolicy
from src.domain.shared.statuses import UserRole
from src.domain.users.profile.entity import UserProfile
from src.domain.users.profile.policies import ActorContext, AdminPolicy, SelfServicePolicy
from src.domain.users.profile.value_objects import DisplayName, Email, Phone


def _profile() -> UserProfile:
    now = datetime(2026, 4, 9, tzinfo=UTC)
    return UserProfile.create(
        user_id="u-1",
        email=Email("u1@example.com"),
        display_name=DisplayName("User 1"),
        phone=Phone("+995555111222"),
        initial_roles={UserRole.STUDENT},
        now=now,
        actor_id="admin-1",
    )


def test_profile_entity_noop_and_restore_branches() -> None:
    now = datetime(2026, 4, 9, tzinfo=UTC)
    profile = _profile()

    # no-op: роль уже активна
    profile.assign_role(role=UserRole.STUDENT, now=now, actor_id="admin-1")

    # no-op: роль отсутствует
    profile.revoke_role(role=UserRole.TEACHER, now=now, actor_id="admin-1")

    with pytest.raises(InvariantViolationError):
        profile.restore(now=now, actor_id="admin-1")


def test_policies_and_value_objects_extra_branches() -> None:
    admin = ActorContext(actor_id="admin-1", roles={UserRole.ADMIN})
    AdminPolicy.ensure_can_manage_users(admin)

    with pytest.raises(AccessDeniedError):
        AdminPolicy.ensure_can_manage_users(ActorContext(actor_id="u-1", roles={UserRole.STUDENT}))

    SelfServicePolicy.ensure_can_edit_profile(admin, target_user_id="u-2")

    with pytest.raises(AccessDeniedError):
        ParentStudentLinkPolicy.ensure_can_remove_link(
            ActorContext(actor_id="u-1", roles={UserRole.PARENT}),
            parent_id="u-2",
        )

    with pytest.raises(InvariantViolationError):
        DisplayName(" " )
    with pytest.raises(InvariantViolationError):
        Email("bad")
    with pytest.raises(InvariantViolationError):
        Phone("abc")
