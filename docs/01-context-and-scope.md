# Bounded Context И Границы

## Название Контекста

**Контекст Управления Пользователями**

## Назначение Контекста

Контекст управляет профилями пользователей, назначением ролей и связями родитель-ученик.
Он обеспечивает консистентность жизненного цикла пользователей и role-aware решения доступа для сценариев платформы.

## Ответственность

Контекст обязан:
1. управлять жизненным циклом `UserProfile`
2. назначать/снимать поддерживаемые роли
3. управлять жизненным циклом `ParentStudentLink`
4. обеспечивать инварианты отношений и статусов
5. предоставлять read/write API для потребителей платформы
6. публиковать события пользовательского домена

## Структура Агрегатов

```shell
UserProfile (Aggregate Root)
|- RoleAssignment (Entity)
`- UserStatus (Value Object)

ParentStudentLink (Aggregate Root)
`- LinkStatus (Value Object)
```

## Внешние Зависимости

Зависит от:
- `auth_service` для actor identity и role claims
- persistence/messaging адаптеров через порты

Не зависит от:
- механики выдачи auth токенов
- логики course/assessment
- деталей HTTP-фреймворка в domain/application

## Точки Интеграции

Входящие:
- admin-операции по user governance
- пользовательские profile-операции
- операции связей parent-student

Исходящие:
- user events (`user.created`, `role.changed`, `status.changed`)
- link events (`parent_student_link.created`, `removed`)

## Явные Границы

Контекст не должен:
- выпускать/обновлять/отзывать токены
- хранить парольные credentials
- напрямую изменять данные внешних сервисов
