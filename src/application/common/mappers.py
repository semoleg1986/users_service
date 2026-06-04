"""Мапперы доменных агрегатов в application DTO."""

from __future__ import annotations

from src.application.common.dto import (
    ParentStudentLinkResult,
    StaffInviteResult,
    StudentInviteResult,
    UserProfileResult,
)
from src.domain.links.parent_student_link.entity import ParentStudentLink
from src.domain.links.staff_invite.entity import StaffInvite
from src.domain.links.student_invite.entity import StudentInvite
from src.domain.users.profile.entity import UserProfile


def to_user_profile_result(profile: UserProfile) -> UserProfileResult:
    """Преобразует UserProfile в UserProfileResult."""

    return UserProfileResult(
        user_id=profile.user_id,
        email=profile.email.value,
        display_name=profile.display_name.value,
        phone=profile.phone.value if profile.phone else None,
        status=profile.status.value,
        roles=sorted(role.value for role in profile.roles),
        created_at=profile.meta.created_at,
        updated_at=profile.meta.updated_at,
        version=profile.meta.version,
    )


def to_link_result(link: ParentStudentLink) -> ParentStudentLinkResult:
    """Преобразует ParentStudentLink в ParentStudentLinkResult."""

    return ParentStudentLinkResult(
        link_id=link.link_id,
        parent_id=link.parent_id,
        student_id=link.student_id,
        status=link.status.value,
        note=link.note.value if link.note else None,
        created_at=link.meta.created_at,
        updated_at=link.meta.updated_at,
        version=link.meta.version,
    )


def to_student_invite_result(
    invite: StudentInvite, *, invite_token: str | None = None
) -> StudentInviteResult:
    """Преобразует StudentInvite в StudentInviteResult."""

    return StudentInviteResult(
        invite_id=invite.invite_id,
        parent_user_id=invite.parent_user_id,
        student_user_id=invite.student_user_id,
        email=invite.email,
        status=invite.status.value,
        expires_at=invite.expires_at,
        used_at=invite.used_at,
        revoked_at=invite.revoked_at,
        created_at=invite.meta.created_at,
        updated_at=invite.meta.updated_at,
        version=invite.meta.version,
        invite_token=invite_token,
    )


def to_staff_invite_result(
    invite: StaffInvite, *, invite_token: str | None = None
) -> StaffInviteResult:
    """Преобразует StaffInvite в StaffInviteResult."""

    return StaffInviteResult(
        invite_id=invite.invite_id,
        creator_user_id=invite.creator_user_id,
        target_user_id=invite.target_user_id,
        email=invite.email,
        roles=sorted(role.value for role in invite.roles),
        status=invite.status.value,
        expires_at=invite.expires_at,
        used_at=invite.used_at,
        revoked_at=invite.revoked_at,
        created_at=invite.meta.created_at,
        updated_at=invite.meta.updated_at,
        version=invite.meta.version,
        invite_token=invite_token,
    )
