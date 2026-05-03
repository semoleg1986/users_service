"""Маппинг исключений в RFC7807."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.domain.errors import AccessDeniedError, InvariantViolationError
from src.interface.http.problem_types import (
    PROBLEM_ACCESS_DENIED,
    PROBLEM_CONFLICT,
    PROBLEM_VALIDATION,
)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _correlation_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None)


def _problem(
    *,
    request: Request,
    status: int,
    title: str,
    detail: str,
    problem_type: str,
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
        headers={
            **(
                {"X-Request-ID": _request_id(request)}
                if _request_id(request) is not None
                else {}
            ),
            **(
                {"X-Correlation-ID": _correlation_id(request)}
                if _correlation_id(request) is not None
                else {}
            ),
        },
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
