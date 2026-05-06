"""Composition root users_service."""

from __future__ import annotations

from dataclasses import dataclass

from src.application.facade.application_facade import ApplicationFacade
from src.application.links.commands.dto import (
    CreateParentStudentLinkCommand,
    RemoveParentStudentLinkCommand,
)
from src.application.links.handlers.create_parent_student_link_handler import (
    CreateParentStudentLinkHandler,
    ListParentStudentLinksHandler,
    RemoveParentStudentLinkHandler,
)
from src.application.links.queries.dto import ListParentStudentLinksQuery
from src.application.ports.access_token_verifier import AccessTokenVerifier
from src.application.users.commands.dto import (
    AssignRoleCommand,
    ChangeUserStatusCommand,
    CreateUserProfileCommand,
    RevokeRoleCommand,
    UpdateUserProfileCommand,
)
from src.application.users.handlers.create_user_profile_handler import (
    CreateUserProfileHandler,
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
from src.infrastructure.auth.jwks_access_token_verifier import JwksAccessTokenVerifier
from src.infrastructure.clock.system_clock import SystemClock
from src.infrastructure.config.settings import Settings
from src.infrastructure.db.inmemory.repositories import (
    InMemoryParentStudentLinkRepository,
    InMemoryUserProfileRepository,
)
from src.infrastructure.db.inmemory.uow import (
    InMemoryRepositoryProvider,
    InMemoryUnitOfWork,
)
from src.infrastructure.id.uuid_generator import UuidGenerator


@dataclass(frozen=True, slots=True)
class RuntimeContainer:
    """Контейнер runtime-зависимостей."""

    facade: ApplicationFacade
    access_token_verifier: AccessTokenVerifier
    service_token: str


def build_runtime() -> RuntimeContainer:
    """Собирает runtime-граф зависимостей."""

    settings = Settings.from_env()
    access_token_verifier = JwksAccessTokenVerifier(
        issuer=settings.auth_issuer,
        audience=settings.auth_audience,
        jwks_url=settings.auth_jwks_url,
        jwks_json=settings.auth_jwks_json,
    )
    if settings.use_inmemory:
        uow = InMemoryUnitOfWork(
            InMemoryRepositoryProvider(
                user_profiles=InMemoryUserProfileRepository(),
                parent_student_links=InMemoryParentStudentLinkRepository(),
            )
        )
        uow_factory = lambda: uow
    else:
        from src.infrastructure.db.sqlalchemy import models as _models  # noqa: F401
        from src.infrastructure.db.sqlalchemy.base import Base
        from src.infrastructure.db.sqlalchemy.session import (
            build_engine,
            build_session_factory,
        )
        from src.infrastructure.db.sqlalchemy.uow.sqlalchemy_uow import (
            SqlAlchemyUnitOfWork,
        )

        engine = build_engine(settings.database_url)
        if settings.auto_create_schema:
            Base.metadata.create_all(bind=engine)
        session_factory = build_session_factory(engine)
        uow_factory = lambda: SqlAlchemyUnitOfWork(session_factory)

    clock = SystemClock()
    id_generator = UuidGenerator()

    facade = ApplicationFacade()
    facade.register_command_handler(
        CreateUserProfileCommand,
        CreateUserProfileHandler(
            uow_factory=uow_factory,
            clock=clock,
            id_generator=id_generator,
        ),
    )
    facade.register_command_handler(
        CreateParentStudentLinkCommand,
        CreateParentStudentLinkHandler(
            uow_factory=uow_factory,
            clock=clock,
            id_generator=id_generator,
        ),
    )
    facade.register_command_handler(
        UpdateUserProfileCommand,
        UpdateUserProfileHandler(uow_factory=uow_factory, clock=clock),
    )
    facade.register_command_handler(
        AssignRoleCommand,
        AssignRoleHandler(uow_factory=uow_factory, clock=clock),
    )
    facade.register_command_handler(
        RevokeRoleCommand,
        RevokeRoleHandler(uow_factory=uow_factory, clock=clock),
    )
    facade.register_command_handler(
        ChangeUserStatusCommand,
        ChangeUserStatusHandler(uow_factory=uow_factory, clock=clock),
    )
    facade.register_command_handler(
        RemoveParentStudentLinkCommand,
        RemoveParentStudentLinkHandler(uow_factory=uow_factory, clock=clock),
    )
    facade.register_query_handler(
        GetUserByIdQuery, GetUserByIdHandler(uow_factory=uow_factory)
    )
    facade.register_query_handler(
        ListUsersQuery, ListUsersHandler(uow_factory=uow_factory)
    )
    facade.register_query_handler(
        GetMyProfileQuery, GetMyProfileHandler(uow_factory=uow_factory)
    )
    facade.register_query_handler(
        ListParentStudentsQuery,
        ListParentStudentsHandler(uow_factory=uow_factory),
    )
    facade.register_query_handler(
        ListParentStudentLinksQuery,
        ListParentStudentLinksHandler(uow_factory=uow_factory),
    )
    return RuntimeContainer(
        facade=facade,
        access_token_verifier=access_token_verifier,
        service_token=settings.service_token,
    )
