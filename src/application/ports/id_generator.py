"""Порт генерации идентификаторов."""

from __future__ import annotations

from typing import Protocol


class IdGenerator(Protocol):
    """Контракт генератора идентификаторов."""

    def new(self) -> str:
        """Возвращает новый идентификатор."""

