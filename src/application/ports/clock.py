"""Порт времени."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Контракт времени application-слоя."""

    def now(self) -> datetime:
        """Возвращает текущее UTC-время."""

