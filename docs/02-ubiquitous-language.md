# Ubiquitous Language

## Базовые Термины

### UserProfile
Корневой агрегат, представляющий пользователя платформы в бизнес-домене.

### RoleAssignment
Сущность, фиксирующая метаданные назначения роли и ее lifecycle.

### UserStatus
Value object enum: `active | blocked | archived`.

### ParentStudentLink
Корневой агрегат подтвержденной связи между пользователем-родителем и пользователем-учеником.

### LinkStatus
Value object enum жизненного цикла связи.

### Actor
Контекст аутентифицированного вызывающего, используемый в политиках доступа.

### AccessPolicy
Доменная политика авторизации операций.

## Запрещенные Термины

| Термин | Причина |
|---|---|
| credential owner | credentials принадлежат `auth_service` |
| direct role sql patch | изменения ролей должны проходить через доменные политики |
| implicit parent access | нужен явный `ParentStudentLink` |
