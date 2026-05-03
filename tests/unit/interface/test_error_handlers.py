from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError

from src.domain.errors import AccessDeniedError
from src.interface.http.errors import register_exception_handlers
from src.interface.http.observability import install_observability


def test_http_error_handlers_cover_access_and_validation_cases() -> None:
    app = FastAPI()
    install_observability(app)
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

    denied = client.get(
        "/denied",
        headers={
            "X-Request-ID": "req-users-001",
            "X-Correlation-ID": "corr-users-001",
        },
    )
    assert denied.status_code == 403
    assert denied.headers.get("X-Request-ID") == "req-users-001"
    assert denied.headers.get("X-Correlation-ID") == "corr-users-001"
    assert denied.json().get("request_id") == "req-users-001"
    assert denied.json().get("correlation_id") == "corr-users-001"

    pyd = client.get("/pydantic")
    assert pyd.status_code == 422

    req = client.get("/ok", params={"q": "bad"})
    assert req.status_code == 422
