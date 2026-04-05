# Формат Ошибок (RFC 7807)

`users_service` возвращает ошибки как `application/problem+json`.

## Формат Ответа

- `type`
- `title`
- `status`
- `detail`
- `instance` (опционально)
- `request_id` (рекомендуется)

## Стандартные Типы Проблем

- `/problems/validation` -> `422`
- `/problems/not-found` -> `404`
- `/problems/access-denied` -> `403`
- `/problems/conflict` -> `409`
- `/problems/unauthorized` -> `401`

## Маппинг Исключений

- `ValidationError` -> `422`
- `NotFoundError` -> `404`
- `AccessDeniedError` -> `403`
- `InvariantViolationError` -> `409`
