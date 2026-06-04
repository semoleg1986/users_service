# users_service

User domain service for parent and student profiles.

## Responsibility

`users_service` owns:
- user profiles for `parent`, `student`, `teacher`, `admin`
- parent-student links
- role assignment and profile status changes
- student/staff invite metadata for identity onboarding
- self-bootstrap profile endpoint for authenticated users

It is the source of truth for parent/student relationships.

## Invite onboarding contracts

Student onboarding:
- `POST /v1/parent/me/students/{student_id}/invite`
- `POST /internal/v1/student-invites/consume`

Studio/staff onboarding:
- `POST /v1/admin/users/{user_id}/staff-invite`
- Target profile must already be `active` and have at least one staff role:
  `admin`, `teacher`, or `content_manager`.
- `POST /internal/v1/staff-invites/consume`

Unified auth-facing consume endpoint:
- `POST /internal/v1/invites/consume`
- Response contains `invite_type`, `user_id`, `email`, `roles`, and
  `consumed_at`.

Invariant: `auth_service` must create the account with exactly the same
`user_id` returned by users_service invite consume.

## Local run

### Install
```bash
make install
```

### Run with uvicorn
```bash
uvicorn src.interface.http.main:app --host 0.0.0.0 --port 8002 --reload
```

### Health
```bash
curl -fsS http://127.0.0.1:8002/healthz
```

## Environment

- [users_service/.env.example](/Users/olegsemenov/Programming/curs/users_service/.env.example)
- [users_service/.env.local.example](/Users/olegsemenov/Programming/curs/users_service/.env.local.example)

Key variables:
- `USERS_DATABASE_URL`
- `USERS_USE_INMEMORY`
- `USERS_AUTH_ISSUER`
- `USERS_AUTH_AUDIENCE`
- `USERS_AUTH_JWKS_URL`
- `USERS_AUTH_JWKS_JSON`

## Tests and quality

```bash
make test
make test-integration
make lint
make format
```

## Migrations

```bash
make migrate-up
make migrate-down-1
```

## Documentation

Contract and architecture docs:
- [00-vision.md](/Users/olegsemenov/Programming/curs/users_service/docs/00-vision.md)
- [08-interface-layer.md](/Users/olegsemenov/Programming/curs/users_service/docs/08-interface-layer.md)
- [09-infrastructure-layer.md](/Users/olegsemenov/Programming/curs/users_service/docs/09-infrastructure-layer.md)
- [adr/0001-bounded-context.md](/Users/olegsemenov/Programming/curs/users_service/docs/adr/0001-bounded-context.md)
