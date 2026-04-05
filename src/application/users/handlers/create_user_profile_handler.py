"""Handler создания профиля пользователя."""

from __future__ import annotations

from src.application.common.dto import UserProfileResult
from src.application.common.mappers import to_user_profile_result
from src.application.ports.clock import Clock
from src.application.ports.id_generator import IdGenerator
from src.application.ports.unit_of_work import UnitOfWork
from src.application.users.commands.dto import CreateUserProfileCommand
from src.domain.errors import InvariantViolationError
from src.domain.shared.statuses import UserRole
from src.domain.users.profile.entity import UserProfile
from src.domain.users.profile.value_objects import DisplayName, Email, Phone


class CreateUserProfileHandler:
    """Создает профиль пользователя и сохраняет его в репозитории."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._id_generator = id_generator

    def __call__(self, command: CreateUserProfileCommand) -> UserProfileResult:
        existing = self._uow.repositories.user_profiles.get_by_email(command.email)
        if existing is not None:
            raise InvariantViolationError("Пользователь с таким email уже существует.")

        now = self._clock.now()
        user_id = command.user_id or self._id_generator.new()
        profile = UserProfile.create(
            user_id=user_id,
            email=Email(command.email),
            display_name=DisplayName(command.display_name),
            phone=Phone(command.phone) if command.phone else None,
            initial_roles={UserRole(role) for role in command.roles},
            now=now,
            actor_id=command.actor_id,
        )
        self._uow.repositories.user_profiles.save(profile)
        self._uow.commit()
        return to_user_profile_result(profile)
