"""Handler создания student profile для текущего parent."""

from __future__ import annotations

from src.application.common.dto import UserProfileResult
from src.application.common.mappers import to_user_profile_result
from src.application.ports.clock import Clock
from src.application.ports.id_generator import IdGenerator
from src.application.ports.unit_of_work import UnitOfWorkFactory
from src.application.users.commands.dto import CreateMyStudentCommand
from src.domain.errors import InvariantViolationError
from src.domain.links.parent_student_link.entity import ParentStudentLink
from src.domain.links.parent_student_link.policies import ParentStudentLinkPolicy
from src.domain.links.parent_student_link.value_objects import LinkNote
from src.domain.shared.statuses import UserRole
from src.domain.users.profile.entity import UserProfile
from src.domain.users.profile.parent_managed_student_policy import (
    ParentManagedStudentPolicy,
)
from src.domain.users.profile.policies import ActorContext
from src.domain.users.profile.value_objects import DisplayName, Email, Phone


class CreateMyStudentHandler:
    """Создает student profile и активную parent-student связь."""

    def __init__(
        self,
        *,
        uow_factory: UnitOfWorkFactory,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._id_generator = id_generator

    def __call__(self, command: CreateMyStudentCommand) -> UserProfileResult:
        actor = ActorContext.from_claims(command.actor_id, command.actor_roles)
        ParentStudentLinkPolicy.ensure_can_create_link(
            actor, parent_id=command.actor_id
        )

        with self._uow_factory() as uow:
            parent_profile = uow.repositories.user_profiles.get(command.actor_id)
            if parent_profile is None:
                raise InvariantViolationError("Parent профиль не найден.")
            ParentManagedStudentPolicy.ensure_parent_can_create_student(parent_profile)

            existing = uow.repositories.user_profiles.get_by_email(command.email)
            if existing is not None:
                raise InvariantViolationError(
                    "Пользователь с таким email уже существует."
                )

            now = self._clock.now()
            student_user_id = self._id_generator.new()
            student_profile = UserProfile.create(
                user_id=student_user_id,
                email=Email(command.email),
                display_name=DisplayName(command.display_name),
                phone=Phone(command.phone) if command.phone else None,
                initial_roles={UserRole.STUDENT},
                now=now,
                actor_id=command.actor_id,
            )
            uow.repositories.user_profiles.save(student_profile)

            link = ParentStudentLink.request(
                link_id=self._id_generator.new(),
                parent_id=command.actor_id,
                student_id=student_user_id,
                now=now,
                actor_id=command.actor_id,
                note=LinkNote("created-by-parent"),
            )
            link.activate(now=now, actor_id=command.actor_id)
            uow.repositories.parent_student_links.save(link)

            uow.commit()
            return to_user_profile_result(student_profile)
