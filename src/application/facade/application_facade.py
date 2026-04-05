"""Единый фасад use-case handlers."""

from __future__ import annotations

from typing import Any, Callable


class ApplicationFacade:
    """Единая точка входа interface-слоя в application-слой."""

    def __init__(self) -> None:
        self._command_handlers: dict[type, Callable[[Any], Any]] = {}
        self._query_handlers: dict[type, Callable[[Any], Any]] = {}

    def register_command_handler(
        self, command_type: type, handler: Callable[[Any], Any]
    ) -> None:
        """Регистрирует command handler."""

        self._command_handlers[command_type] = handler

    def register_query_handler(self, query_type: type, handler: Callable[[Any], Any]) -> None:
        """Регистрирует query handler."""

        self._query_handlers[query_type] = handler

    def execute(self, command: Any) -> Any:
        """Выполняет command."""

        handler = self._command_handlers.get(type(command))
        if handler is None:
            raise LookupError(f"Handler не найден для command: {type(command).__name__}")
        return handler(command)

    def query(self, query: Any) -> Any:
        """Выполняет query."""

        handler = self._query_handlers.get(type(query))
        if handler is None:
            raise LookupError(f"Handler не найден для query: {type(query).__name__}")
        return handler(query)

