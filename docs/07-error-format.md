# Формат Ошибок (RFC 7807)

`users_service` возвращает ошибки как `application/problem+json`.

## Формат Ответа

- `type`
- `title`
- `status`
- `detail`
- `instance`
- `request_id`
- `correlation_id`

`X-Request-ID` и `X-Correlation-ID` также возвращаются в headers, когда доступны.

## Стандартные Типы Проблем

- `/problems/validation` -> `422`
- `/problems/not-found` -> `404`
- `/problems/access-denied` -> `403`
- `/problems/conflict` -> `409`
- `/problems/unauthorized` -> `401`

## Маппинг Исключений

- `ValidationError` -> `422`
- `HTTPException(401)` -> `401`
- `HTTPException(403)` -> `403`
- `HTTPException(404)` -> `404`
- `NotFoundError` -> `404`
- `AccessDeniedError` -> `403`
- `InvariantViolationError` -> `409`
