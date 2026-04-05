# PostgreSQL: запуск users_service

## 1. URL подключения

```bash
export USERS_DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/users_service'
```

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

