"""Composition root users_service."""

from __future__ import annotations

from dataclasses import dataclass

from src.application.facade.application_facade import ApplicationFacade
from src.application.links.commands.dto import CreateParentStudentLinkCommand
from src.application.links.handlers.create_parent_student_link_handler import (
    CreateParentStudentLinkHandler,
    ListParentStudentLinksHandler,
    RemoveParentStudentLinkHandler,
)
from src.application.links.commands.dto import RemoveParentStudentLinkCommand
from src.application.links.queries.dto import ListParentStudentLinksQuery
from src.application.users.commands.dto import (
    AssignRoleCommand,
    ChangeUserStatusCommand,
    CreateUserProfileCommand,
    RevokeRoleCommand,
    UpdateUserProfileCommand,
)
from src.application.users.handlers.get_user_handlers import (
    GetMyProfileHandler,
    GetUserByIdHandler,
    ListParentStudentsHandler,
    ListUsersHandler,
)
from src.application.users.handlers.manage_user_handlers import (
    AssignRoleHandler,
    ChangeUserStatusHandler,
    RevokeRoleHandler,
    UpdateUserProfileHandler,
)
from src.application.users.queries.dto import (
    GetMyProfileQuery,
    GetUserByIdQuery,
    ListParentStudentsQuery,
    ListUsersQuery,
)
from src.application.users.handlers.create_user_profile_handler import (
    CreateUserProfileHandler,
)
from src.infrastructure.clock.system_clock import SystemClock
from src.infrastructure.db.inmemory.repositories import (
    InMemoryParentStudentLinkRepository,
    InMemoryUserProfileRepository,
)
from src.infrastructure.db.inmemory.uow import InMemoryRepositoryProvider, InMemoryUnitOfWork
from src.infrastructure.id.uuid_generator import UuidGenerator


@dataclass(frozen=True, slots=True)
class RuntimeContainer:
    """Контейнер runtime-зависимостей."""

    facade: ApplicationFacade


def build_runtime() -> RuntimeContainer:
    """Собирает runtime-граф зависимостей."""

    uow = InMemoryUnitOfWork(
        InMemoryRepositoryProvider(
            user_profiles=InMemoryUserProfileRepository(),
            parent_student_links=InMemoryParentStudentLinkRepository(),
        )
    )
    clock = SystemClock()
    id_generator = UuidGenerator()

    facade = ApplicationFacade()
    facade.register_command_handler(
        CreateUserProfileCommand,
        CreateUserProfileHandler(uow=uow, clock=clock, id_generator=id_generator),
    )
    facade.register_command_handler(
        CreateParentStudentLinkCommand,
        CreateParentStudentLinkHandler(uow=uow, clock=clock, id_generator=id_generator),
    )
    facade.register_command_handler(
        UpdateUserProfileCommand,
        UpdateUserProfileHandler(uow=uow, clock=clock),
    )
    facade.register_command_handler(
        AssignRoleCommand,
        AssignRoleHandler(uow=uow, clock=clock),
    )
    facade.register_command_handler(
        RevokeRoleCommand,
        RevokeRoleHandler(uow=uow, clock=clock),
    )
    facade.register_command_handler(
        ChangeUserStatusCommand,
        ChangeUserStatusHandler(uow=uow, clock=clock),
    )
    facade.register_command_handler(
        RemoveParentStudentLinkCommand,
        RemoveParentStudentLinkHandler(uow=uow, clock=clock),
    )
    facade.register_query_handler(GetUserByIdQuery, GetUserByIdHandler(uow=uow))
    facade.register_query_handler(ListUsersQuery, ListUsersHandler(uow=uow))
    facade.register_query_handler(GetMyProfileQuery, GetMyProfileHandler(uow=uow))
    facade.register_query_handler(
        ListParentStudentsQuery,
        ListParentStudentsHandler(uow=uow),
    )
    facade.register_query_handler(
        ListParentStudentLinksQuery,
        ListParentStudentLinksHandler(uow=uow),
    )
    return RuntimeContainer(facade=facade)
