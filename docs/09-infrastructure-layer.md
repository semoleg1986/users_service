# Infrastructure Слой

## Назначение

Infrastructure-слой реализует persistence, messaging и integration adapters для application-портов.

## Структура

```shell
src/infrastructure/
|- db/
|  |- session.py
|  |- models.py
|  |- repositories/
|  |  |- user_profile_repository_sqlalchemy.py
|  |  `- parent_student_link_repository_sqlalchemy.py
|  `- uow/sqlalchemy_uow.py
|- messaging/
|  |- outbox_publisher.py
|  `- event_bus_kafka.py
`- di/
   `- providers.py
```

## Ответственность

- реализовать repository ports и UoW
- публиковать доменные события через outbox/event bus
- предоставлять DI composition root

## Правила Границ

- без HTTP-контрактов
- без use-case orchestration
- без доменной policy-логики
