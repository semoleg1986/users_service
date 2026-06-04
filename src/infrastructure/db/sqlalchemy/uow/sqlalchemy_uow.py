"""SQLAlchemy Unit of Work."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from src.application.ports.repositories import RepositoryProvider
from src.infrastructure.db.sqlalchemy.repositories.parent_student_link_repository_sqlalchemy import (  # noqa: E501
    SqlAlchemyParentStudentLinkRepository,
)
from src.infrastructure.db.sqlalchemy.repositories.staff_invite_repository_sqlalchemy import (  # noqa: E501
    SqlAlchemyStaffInviteRepository,
)
from src.infrastructure.db.sqlalchemy.repositories.student_invite_repository_sqlalchemy import (  # noqa: E501
    SqlAlchemyStudentInviteRepository,
)
from src.infrastructure.db.sqlalchemy.repositories.user_profile_repository_sqlalchemy import (  # noqa: E501
    SqlAlchemyUserProfileRepository,
)


class SqlAlchemyUnitOfWork:
    """SQLAlchemy реализация UnitOfWork."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._db: Session = session_factory()
        self.repositories = RepositoryProvider(
            user_profiles=SqlAlchemyUserProfileRepository(self._db),
            parent_student_links=SqlAlchemyParentStudentLinkRepository(self._db),
            student_invites=SqlAlchemyStudentInviteRepository(self._db),
            staff_invites=SqlAlchemyStaffInviteRepository(self._db),
        )

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc is not None:
            self.rollback()
        self.close()

    def commit(self) -> None:
        self._db.commit()

    def rollback(self) -> None:
        self._db.rollback()

    def close(self) -> None:
        self._db.close()
