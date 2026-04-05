"""Извлечение actor context из HTTP-заголовков."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException


@dataclass(frozen=True, slots=True)
class HttpActor:
    """Контекст актора, извлеченный из заголовков."""

    actor_id: str
    roles: list[str]


def get_http_actor(
    actor_id: str | None = Header(default=None, alias="X-Actor-Id"),
    roles: str | None = Header(default=None, alias="X-Actor-Roles"),
) -> HttpActor:
    """Возвращает actor context из transport заголовков."""

    if not actor_id:
        raise HTTPException(status_code=401, detail="Требуется X-Actor-Id.")
    if not roles:
        raise HTTPException(status_code=401, detail="Требуется X-Actor-Roles.")
    parsed = [item.strip() for item in roles.split(",") if item.strip()]
    if not parsed:
        raise HTTPException(status_code=401, detail="X-Actor-Roles пустой.")
    return HttpActor(actor_id=actor_id, roles=parsed)

