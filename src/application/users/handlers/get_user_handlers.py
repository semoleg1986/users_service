"""Handlers чтения профилей пользователей."""

from __future__ import annotations

from src.application.common.dto import UserProfileResult
from src.application.common.mappers import to_user_profile_result
from src.application.ports.unit_of_work import UnitOfWork
from src.application.users.queries.dto import (
    GetMyProfileQuery,
    GetUserByIdQuery,
    ListParentStudentsQuery,
    ListUsersQuery,
)
from src.domain.errors import AccessDeniedError, InvariantViolationError
from src.domain.shared.statuses import UserRole
from src.domain.users.profile.policies import ActorContext, AdminPolicy


class GetUserByIdHandler:
    """Возвращает профиль пользователя по id."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def __call__(self, query: GetUserByIdQuery) -> UserProfileResult:
        actor = ActorContext.from_claims(query.actor_id, query.actor_roles)
        AdminPolicy.ensure_can_manage_users(actor)
        profile = self._uow.repositories.user_profiles.get(query.user_id)
        if profile is None:
            raise InvariantViolationError("Пользователь не найден.")
        return to_user_profile_result(profile)


class ListUsersHandler:
    """Возвращает список профилей пользователей."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def __call__(self, query: ListUsersQuery) -> list[UserProfileResult]:
        actor = ActorContext.from_claims(query.actor_id, query.actor_roles)
        AdminPolicy.ensure_can_manage_users(actor)
        return [
            to_user_profile_result(p)
            for p in self._uow.repositories.user_profiles.list(
                role=query.role, status=query.status
            )
        ]


class GetMyProfileHandler:
    """Возвращает профиль текущего пользователя."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def __call__(self, query: GetMyProfileQuery) -> UserProfileResult:
        profile = self._uow.repositories.user_profiles.get(query.actor_id)
        if profile is None:
            raise InvariantViolationError("Пользователь не найден.")
        return to_user_profile_result(profile)


class ListParentStudentsHandler:
    """Возвращает список учеников, связанных с parent."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def __call__(self, query: ListParentStudentsQuery) -> list[UserProfileResult]:
        actor = ActorContext.from_claims(query.actor_id, query.actor_roles)
        if UserRole.PARENT not in actor.roles and UserRole.ADMIN not in actor.roles:
            raise AccessDeniedError("Операция доступна parent или admin.")
        links = self._uow.repositories.parent_student_links.list_active_by_parent(query.actor_id)
        result: list[UserProfileResult] = []
        for link in links:
            student = self._uow.repositories.user_profiles.get(link.student_id)
            if student is not None:
                result.append(to_user_profile_result(student))
        return result

