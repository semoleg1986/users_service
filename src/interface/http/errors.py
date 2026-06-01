"""Маппинг исключений в RFC7807."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.domain.errors import AccessDeniedError, InvariantViolationError
from src.interface.http.problem_types import (
    PROBLEM_ACCESS_DENIED,
    PROBLEM_CONFLICT,
    PROBLEM_NOT_FOUND,
    PROBLEM_UNAUTHORIZED,
    PROBLEM_VALIDATION,
)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _correlation_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


def _headers(request: Request, extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = dict(extra or {})
    request_id = _request_id(request)
    correlation_id = _correlation_id(request)
    if request_id is not None:
        headers["X-Request-ID"] = request_id
    if correlation_id is not None:
        headers["X-Correlation-ID"] = correlation_id
    return headers


def _problem(
    *,
    request: Request,
    status: int,
    title: str,
    detail: str,
    problem_type: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "type": problem_type,
            "title": title,
            "status": status,
            "detail": detail,
            "instance": str(request.url.path),
            "request_id": _request_id(request),
            "correlation_id": _correlation_id(request),
        },
        media_type="application/problem+json",
        headers=_headers(request, headers),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Регистрирует обработчики ошибок HTTP слоя."""

    @app.exception_handler(InvariantViolationError)
    async def invariant_error(
        request: Request, exc: InvariantViolationError
    ) -> JSONResponse:
        return _problem(
            request=request,
            status=409,
            title="Нарушение инварианта",
            detail=str(exc),
            problem_type=PROBLEM_CONFLICT,
        )

    @app.exception_handler(AccessDeniedError)
    async def access_denied(request: Request, exc: AccessDeniedError) -> JSONResponse:
        return _problem(
            request=request,
            status=403,
            title="Доступ запрещен",
            detail=str(exc),
            problem_type=PROBLEM_ACCESS_DENIED,
        )

    @app.exception_handler(ValidationError)
    async def validation_error(request: Request, exc: ValidationError) -> JSONResponse:
        return _problem(
            request=request,
            status=422,
            title="Ошибка валидации",
            detail=str(exc),
            problem_type=PROBLEM_VALIDATION,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _problem(
            request=request,
            status=422,
            title="Ошибка валидации",
            detail=str(exc),
            problem_type=PROBLEM_VALIDATION,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        mapping = {
            401: ("Не авторизован", PROBLEM_UNAUTHORIZED),
            403: ("Доступ запрещен", PROBLEM_ACCESS_DENIED),
            404: ("Не найдено", PROBLEM_NOT_FOUND),
            409: ("Конфликт", PROBLEM_CONFLICT),
            422: ("Ошибка валидации", PROBLEM_VALIDATION),
        }
        title, problem_type = mapping.get(
            exc.status_code, (str(exc.detail), "about:blank")
        )
        return _problem(
            request=request,
            status=exc.status_code,
            title=title,
            detail=str(exc.detail),
            problem_type=problem_type,
            headers=exc.headers,
        )
