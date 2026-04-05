# Доменная Модель

## Назначение

Определяет границы агрегатов, сущности, value objects и репозиторные порты для `users_service`.

## Структура Домена

```shell
src/domain/
|- users/
|  `- profile/
|     |- entity.py
|     |- value_objects.py
|     |- repository.py
|     |- events.py
|     `- policies.py
|- links/
|  `- parent_student_link/
|     |- entity.py
|     |- value_objects.py
|     |- repository.py
|     |- events.py
|     `- policies.py
|- shared/
|  |- entity.py
|  `- statuses.py
`- errors.py
```

## Корневые Агрегаты

### `UserProfile` (Aggregate Root)
Владеет полями профиля, назначениями ролей и lifecycle-статусом.

### `ParentStudentLink` (Aggregate Root)
Владеет статусом связи и инвариантами между `parent_id` и `student_id`.

## Сущности

- `RoleAssignment`

## Value Objects

- `UserStatus`, `LinkStatus`, `DisplayName`, `Email`, `Phone` (по необходимости)

## Репозиторные Порты

- `UserProfileRepository`
- `ParentStudentLinkRepository`

## Доменные События

- `UserCreated`
- `UserRoleChanged`
- `UserStatusChanged`
- `ParentStudentLinkCreated`
- `ParentStudentLinkRemoved`
