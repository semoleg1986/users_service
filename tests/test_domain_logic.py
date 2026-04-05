from datetime import UTC, datetime

import pytest

from src.domain.errors import AccessDeniedError, InvariantViolationError
from src.domain.links.parent_student_link.entity import ParentStudentLink
from src.domain.links.parent_student_link.policies import ParentStudentLinkPolicy
from src.domain.shared.statuses import UserRole, UserStatus
from src.domain.users.profile.entity import UserProfile
from src.domain.users.profile.policies import ActorContext, SelfServicePolicy
from src.domain.users.profile.value_objects import DisplayName, Email, Phone


def test_user_profile_must_have_initial_role() -> None:
    now = datetime.now(UTC)
    with pytest.raises(InvariantViolationError):
        UserProfile.create(
            user_id="u-1",
            email=Email("u1@example.com"),
            display_name=DisplayName("User 1"),
            phone=None,
            initial_roles=set(),
            now=now,
            actor_id="admin-1",
        )


def test_cannot_revoke_last_active_role() -> None:
    now = datetime.now(UTC)
    profile = UserProfile.create(
        user_id="u-1",
        email=Email("u1@example.com"),
        display_name=DisplayName("User 1"),
        phone=Phone("+995555111222"),
        initial_roles={UserRole.STUDENT},
        now=now,
        actor_id="admin-1",
    )
    with pytest.raises(InvariantViolationError):
        profile.revoke_role(role=UserRole.STUDENT, now=now, actor_id="admin-1")


def test_archived_user_cannot_be_activated_or_edited() -> None:
    now = datetime.now(UTC)
    profile = UserProfile.create(
        user_id="u-1",
        email=Email("u1@example.com"),
        display_name=DisplayName("User 1"),
        phone=None,
        initial_roles={UserRole.PARENT},
        now=now,
        actor_id="admin-1",
    )
    profile.archive(now=now, actor_id="admin-1")
    assert profile.status == UserStatus.ARCHIVED

    with pytest.raises(InvariantViolationError):
        profile.activate(now=now, actor_id="admin-1")

    with pytest.raises(InvariantViolationError):
        profile.change_display_name(
            display_name=DisplayName("New Name"),
            now=now,
            actor_id="admin-1",
        )


def test_parent_student_link_cannot_link_same_user() -> None:
    now = datetime.now(UTC)
    with pytest.raises(InvariantViolationError):
        ParentStudentLink.request(
            link_id="l-1",
            parent_id="u-1",
            student_id="u-1",
            now=now,
            actor_id="u-1",
        )


def test_self_service_policy_allows_only_owner_or_admin() -> None:
    actor = ActorContext(actor_id="u-1", roles={UserRole.STUDENT})
    SelfServicePolicy.ensure_can_edit_profile(actor, target_user_id="u-1")
    with pytest.raises(AccessDeniedError):
        SelfServicePolicy.ensure_can_edit_profile(actor, target_user_id="u-2")


def test_parent_link_policy_requires_parent_or_admin() -> None:
    actor = ActorContext(actor_id="teacher-1", roles={UserRole.TEACHER})
    with pytest.raises(AccessDeniedError):
        ParentStudentLinkPolicy.ensure_can_create_link(actor, parent_id="parent-1")

