# Interface Слой

## Назначение

Interface-слой публикует транспортные контракты и делегирует все бизнес-операции в `ApplicationFacade`.

## Структура

```shell
src/interface/http/
|- app.py
|- main.py
|- health.py
|- errors.py
|- problem_types.py
|- wiring.py
`- v1/
   |- internal/router.py
   |- admin/router.py
   |- user/router.py
   `- schemas/
      |- internal.py
      |- users.py
      `- links.py
```

## Ответственность

- request/response DTO валидация
- извлечение actor context
- проверка `X-Service-Token` для internal межсервисных endpoint-ов
- RFC7807 error mapping
- вызов методов application facade

## Правила Границ

- без прямого доступа к repository/DB
- без доменной логики инвариантов
- без утечек infrastructure wiring в handlers
