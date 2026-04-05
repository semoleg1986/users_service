# PostgreSQL: запуск users_service

## 1. URL подключения

```bash
export USERS_DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/users_service'
```

Быстрый старт через шаблоны env:

```bash
cp .env.local.example .env
```

Выберите профиль `dev-postgres` и оставьте только его переменные.

## 2. Режим хранилища

```bash
export USERS_USE_INMEMORY=0
```

Опционально для dev:

```bash
export USERS_AUTO_CREATE_SCHEMA=1
```

## 3. Миграции

```bash
make migrate-up
```

Откат на одну миграцию:

```bash
make migrate-down-1
```

## 4. Локальный запуск API

```bash
uvicorn src.interface.http.main:app --reload
```

## 5. Auth/JWKS

Для проверки Bearer JWT укажите:

```bash
export USERS_AUTH_ISSUER='auth_service'
export USERS_AUTH_JWKS_URL='http://localhost:8000/.well-known/jwks.json'
```

Если `auth_service` не поднят, можно использовать встроенный JSON:

```bash
export USERS_AUTH_JWKS_JSON='{"keys":[...]}'
```
