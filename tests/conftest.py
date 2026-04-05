from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def force_inmemory_for_non_integration(request: pytest.FixtureRequest) -> None:
    """Фиксирует in-memory режим для обычных тестов, не затрагивая integration."""

    if request.node.get_closest_marker("integration"):
        return

    os.environ["USERS_USE_INMEMORY"] = "1"
    os.environ.pop("USERS_DATABASE_URL", None)
    os.environ["USERS_AUTO_CREATE_SCHEMA"] = "0"
