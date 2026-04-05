"""Контракты агрегированных репозиториев."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.links.parent_student_link.repository import ParentStudentLinkRepository
from src.domain.users.profile.repository import UserProfileRepository


@dataclass(frozen=True, slots=True)
class RepositoryProvider:
    """Набор репозиториев в рамках UoW."""

    user_profiles: UserProfileRepository
    parent_student_links: ParentStudentLinkRepository

