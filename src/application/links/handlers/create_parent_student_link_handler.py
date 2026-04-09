"""Handler создания связи parent-student."""

from __future__ import annotations

from src.application.common.dto import ParentStudentLinkResult
from src.application.common.mappers import to_link_result
from src.application.links.commands.dto import (
    CreateParentStudentLinkCommand,
    RemoveParentStudentLinkCommand,
)
from src.application.links.queries.dto import ListParentStudentLinksQuery
from src.application.ports.clock import Clock
from src.application.ports.id_generator import IdGenerator
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.errors import InvariantViolationError
from src.domain.links.parent_student_link.entity import ParentStudentLink
from src.domain.links.parent_student_link.policies import ParentStudentLinkPolicy
from src.domain.links.parent_student_link.value_objects import LinkNote
from src.domain.shared.statuses import UserRole, UserStatus
from src.domain.users.profile.policies import AdminPolicy
from src.domain.users.profile.policies import ActorContext


class CreateParentStudentLinkHandler:
    """Создает связь parent-student c учетом доменных политик."""

    def __init__(self, *, uow: UnitOfWork, clock: Clock, id_generator: IdGenerator) -> None:
        self._uow = uow
        self._clock = clock
        self._id_generator = id_generator

    def __call__(self, command: CreateParentStudentLinkCommand) -> ParentStudentLinkResult:
        actor = ActorContext.from_claims(
            actor_id=command.actor_id,
            roles=command.actor_roles,
        )
        ParentStudentLinkPolicy.ensure_can_create_link(actor, parent_id=command.parent_id)

        parent_profile = self._uow.repositories.user_profiles.get(command.parent_id)
        student_profile = self._uow.repositories.user_profiles.get(command.student_id)
        if parent_profile is None or student_profile is None:
            raise InvariantViolationError("Parent или student профиль не найден.")
        if UserRole.PARENT not in parent_profile.roles:
            raise InvariantViolationError("Связь можно создать только с пользователем роли parent.")
        if UserRole.STUDENT not in student_profile.roles:
            raise InvariantViolationError("Связь можно создать только с пользователем роли student.")
        if parent_profile.status != UserStatus.ACTIVE or student_profile.status != UserStatus.ACTIVE:
            raise InvariantViolationError(
                "Связь доступна только для пользователей в статусе active."
            )

        if self._uow.repositories.parent_student_links.get_active_by_pair(
            command.parent_id,
            command.student_id,
        ):
            raise InvariantViolationError("Активная связь parent-student уже существует.")

        now = self._clock.now()
        link = ParentStudentLink.request(
            link_id=command.link_id or self._id_generator.new(),
            parent_id=command.parent_id,
            student_id=command.student_id,
            now=now,
            actor_id=command.actor_id,
            note=LinkNote(command.note) if command.note else None,
        )
        link.activate(now=now, actor_id=command.actor_id)
        self._uow.repositories.parent_student_links.save(link)
        self._uow.commit()
        return to_link_result(link)


class RemoveParentStudentLinkHandler:
    """Удаляет связь parent-student."""

    def __init__(self, *, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    def __call__(self, command: RemoveParentStudentLinkCommand) -> ParentStudentLinkResult:
        link = self._uow.repositories.parent_student_links.get(command.link_id)
        if link is None:
            raise InvariantViolationError("Связь не найдена.")
        actor = ActorContext.from_claims(command.actor_id, command.actor_roles)
        ParentStudentLinkPolicy.ensure_can_remove_link(actor, parent_id=link.parent_id)
        link.remove(now=self._clock.now(), actor_id=command.actor_id)
        self._uow.repositories.parent_student_links.save(link)
        self._uow.commit()
        return to_link_result(link)


class ListParentStudentLinksHandler:
    """Возвращает список связей parent-student."""

    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    def __call__(self, query: ListParentStudentLinksQuery) -> list[ParentStudentLinkResult]:
        actor = ActorContext.from_claims(query.actor_id, query.actor_roles)
        AdminPolicy.ensure_can_manage_users(actor)
        return [
            to_link_result(link)
            for link in self._uow.repositories.parent_student_links.list(
                parent_id=query.parent_id,
                student_id=query.student_id,
            )
        ]
