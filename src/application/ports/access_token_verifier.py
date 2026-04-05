"""Порт верификации access token."""

from __future__ import annotations

from typing import Protocol


class AccessTokenVerifier(Protocol):
    """Контракт декодирования и верификации access token."""

    def decode_access(self, access_token: str) -> dict[str, str | list[str]]:
        """Возвращает claims `sub` и `roles` из access token."""

