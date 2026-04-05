"""Мапперы доменных агрегатов в application DTO."""

from __future__ import annotations

from src.application.common.dto import ParentStudentLinkResult, UserProfileResult
from src.domain.links.parent_student_link.entity import ParentStudentLink
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

