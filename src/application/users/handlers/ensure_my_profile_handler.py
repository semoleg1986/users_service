"""Handler идемпотентного bootstrap профиля текущего пользователя."""

from __future__ import annotations

from src.application.common.dto import UserProfileResult
from src.application.common.mappers import to_user_profile_result
from src.application.ports.clock import Clock
from src.application.ports.unit_of_work import UnitOfWorkFactory
from src.application.users.commands.dto import EnsureMyProfileCommand
from src.domain.errors import InvariantViolationError
from src.domain.shared.statuses import UserRole
from src.domain.users.profile.entity import UserProfile
from src.domain.users.profile.value_objects import DisplayName, Email, Phone


class EnsureMyProfileHandler:
    """Создает профиль текущего пользователя, если он отсутствует."""

    def __init__(self, *, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def __call__(self, command: EnsureMyProfileCommand) -> UserProfileResult:
        with self._uow_factory() as uow:
            existing = uow.repositories.user_profiles.get(command.actor_id)
            if existing is not None:
                return to_user_profile_result(existing)

            duplicate = uow.repositories.user_profiles.get_by_email(command.email)
            if duplicate is not None and duplicate.user_id != command.actor_id:
                raise InvariantViolationError(
                    "Пользователь с таким email уже существует."
                )

            now = self._clock.now()
            roles = {UserRole(role) for role in command.actor_roles}
            profile = UserProfile.create(
                user_id=command.actor_id,
                email=Email(command.email),
                display_name=DisplayName(
                    command.display_name or command.email.split("@", 1)[0]
                ),
                phone=Phone(command.phone) if command.phone else None,
                initial_roles=roles,
                now=now,
                actor_id=command.actor_id,
            )
            uow.repositories.user_profiles.save(profile)
            uow.commit()
            return to_user_profile_result(profile)
