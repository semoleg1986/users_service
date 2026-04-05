# Application Слой

## Назначение

Application-слой оркестрирует user/link use cases и предоставляет единый `ApplicationFacade` для interface-адаптеров.

## Структура Application

```shell
src/application/
|- users/
|  |- commands/
|  |- queries/
|  `- handlers/
|- links/
|  |- commands/
|  |- queries/
|  `- handlers/
|- facade/
|  `- application_facade.py
`- ports/
   |- repositories.py
   |- unit_of_work.py
   |- event_bus.py
   |- id_generator.py
   `- clock.py
```

## Command Side (write)

- `CreateUser`, `UpdateUser`
- `AssignRole`, `RevokeRole`
- `BlockUser`, `UnblockUser`, `ArchiveUser`, `RestoreUser`
- `CreateParentStudentLink`, `RemoveParentStudentLink`

## Query Side (read)

- `GetUserById`, `ListUsers`
- `GetParentStudentLinks`, `ListChildrenByParent`

## Контракт Фасада

`ApplicationFacade` — единственная точка входа для interface-слоя и:
- принимает типизированные commands/queries
- возвращает типизированные DTO/errors
- скрывает инфраструктурные реализации

## Порты И Транзакции

- `UnitOfWork` с репозиториями и `commit()/rollback()`
- репозитории для пользователей и связей
- `EventBusPort` для доменных событий

## Границы Слоя

- без HTTP/ORM типов в application-слое
- без бизнес-правил в interface-слое
- без инфраструктурных реализаций в хендлерах
