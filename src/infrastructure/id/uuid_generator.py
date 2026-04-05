"""UUID-реализация генератора идентификаторов."""

from __future__ import annotations

from uuid import uuid4


class UuidGenerator:
    """Генерирует UUID4 идентификаторы."""

    def new(self) -> str:
        """Возвращает новый UUID."""

        return str(uuid4())

