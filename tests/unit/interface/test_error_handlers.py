from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError

from src.domain.errors import AccessDeniedError
from src.interface.http.errors import register_exception_handlers


def test_http_error_handlers_cover_access_and_validation_cases() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/denied")
    def denied() -> None:
        raise AccessDeniedError("forbidden")

    @app.get("/pydantic")
    def pydantic_error() -> None:
        class M(BaseModel):
            value: int

        try:
            M(value="bad")
        except ValidationError as exc:
            raise exc

    @app.get("/ok")
    def ok(q: int) -> dict[str, int]:
        return {"q": q}

    client = TestClient(app)

    denied = client.get("/denied")
    assert denied.status_code == 403

    pyd = client.get("/pydantic")
    assert pyd.status_code == 422

    req = client.get("/ok", params={"q": "bad"})
    assert req.status_code == 422
