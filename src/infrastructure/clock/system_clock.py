"""Системные UTC-часы."""

from __future__ import annotations

from datetime import UTC, datetime


class SystemClock:
    """Реализация порта времени."""

    def now(self) -> datetime:
        """Возвращает текущее время UTC."""

        return datetime.now(UTC)
