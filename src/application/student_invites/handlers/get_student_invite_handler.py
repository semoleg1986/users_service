"""Read handlers для student invites."""

from __future__ import annotations

from src.application.common.dto import StudentInviteResult
from src.application.common.mappers import to_student_invite_result
from src.application.ports.unit_of_work import UnitOfWorkFactory
from src.application.student_invites.queries.dto import GetStudentInviteByIdQuery
from src.domain.errors import AccessDeniedError, InvariantViolationError
from src.domain.shared.statuses import UserRole
from src.domain.users.profile.policies import ActorContext


class GetStudentInviteByIdHandler:
    """Возвращает invite по ID для parent/admin."""

    def __init__(self, *, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    def __call__(self, query: GetStudentInviteByIdQuery) -> StudentInviteResult:
        actor = ActorContext.from_claims(query.actor_id, query.actor_roles)
        if UserRole.ADMIN not in actor.roles and UserRole.PARENT not in actor.roles:
            raise AccessDeniedError("Операция доступна parent или admin.")

        with self._uow_factory() as uow:
            invite = uow.repositories.student_invites.get(query.invite_id)
            if invite is None:
                raise InvariantViolationError("invite не найден.")

            if (
                UserRole.ADMIN not in actor.roles
                and invite.parent_user_id != query.actor_id
            ):
                raise AccessDeniedError("Parent может читать только свои invite.")

            return to_student_invite_result(invite)
