from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


def _database_url() -> str:
    return os.getenv(
        "USERS_DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/users_service_test",
    )


@pytest.fixture(scope="session", autouse=True)
def prepare_postgres_schema() -> None:
    os.environ["USERS_USE_INMEMORY"] = "0"
    os.environ["USERS_AUTO_CREATE_SCHEMA"] = "0"
    database_url = _database_url()
    os.environ["USERS_DATABASE_URL"] = database_url

    try:
        engine = create_engine(database_url, future=True, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"Postgres недоступен для integration tests: {exc}")

    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(autouse=True)
def clean_tables() -> None:
    database_url = _database_url()
    engine = create_engine(database_url, future=True, pool_pre_ping=True)
    with engine.begin() as conn:
        try:
            conn.execute(text("TRUNCATE TABLE staff_invites RESTART IDENTITY CASCADE"))
            conn.execute(
                text("TRUNCATE TABLE student_invites RESTART IDENTITY CASCADE")
            )
            conn.execute(
                text("TRUNCATE TABLE parent_student_links RESTART IDENTITY CASCADE")
            )
            conn.execute(text("TRUNCATE TABLE user_profiles RESTART IDENTITY CASCADE"))
        except SQLAlchemyError:
            conn.execute(text("DELETE FROM staff_invites"))
            conn.execute(text("DELETE FROM student_invites"))
            conn.execute(text("DELETE FROM parent_student_links"))
            conn.execute(text("DELETE FROM user_profiles"))
