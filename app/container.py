"""
DI-контейнер (реестр сервисов).

Поддерживает:
- register(name, instance) — немедленная регистрация
- register_lazy(name, factory) — ленивая инициализация при первом обращении
- container.name — доступ через __getattr__
- shutdown() — упорядоченное закрытие ресурсов
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class Container:
    def __init__(self) -> None:
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._shutdown_order: List[str] = []

    # ── Регистрация ───────────────────────────────────────────────────

    def register(self, name: str, instance: Any) -> None:
        """Регистрирует готовый экземпляр сервиса."""
        if name in self._services or name in self._factories:
            raise ValueError(f"Service '{name}' already registered")
        self._services[name] = instance
        self._shutdown_order.append(name)

    def register_lazy(self, name: str, factory: Callable[[], Any]) -> None:
        """
        Регистрирует фабрику — сервис будет создан при первом обращении.
        
        factory — callable без аргументов, возвращающий экземпляр сервиса.
        """
        if name in self._services or name in self._factories:
            raise ValueError(f"Service '{name}' already registered")
        self._factories[name] = factory
        self._shutdown_order.append(name)

    # ── Получение ─────────────────────────────────────────────────────

    def get(self, name: str) -> Any:
        """Возвращает сервис по имени. Для lazy — создаёт при первом вызове."""
        # Уже инициализирован
        if name in self._services:
            return self._services[name]

        # Ленивая инициализация
        if name in self._factories:
            logger.info("Lazy init: создание сервиса '%s'", name)
            instance = self._factories.pop(name)()
            self._services[name] = instance
            return instance

        raise ValueError(f"Service '{name}' not found")

    def __getattr__(self, name: str) -> Any:
        """Позволяет обращаться как container.gemini_service."""
        # Защита от рекурсии при обращении к внутренним атрибутам
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self.get(name)
        except ValueError:
            raise AttributeError(f"Service '{name}' not found in container")

    def has(self, name: str) -> bool:
        """Проверяет, зарегистрирован ли сервис (включая lazy)."""
        return name in self._services or name in self._factories

    # ── Shutdown ──────────────────────────────────────────────────────

    async def shutdown(self) -> None:
        """
        Упорядоченное закрытие ресурсов (в обратном порядке регистрации).
        
        Вызывает close()/shutdown()/disconnect() если они есть у сервиса.
        """
        for name in reversed(self._shutdown_order):
            service = self._services.get(name)
            if service is None:
                continue  # lazy, но так и не был создан

            for method_name in ("shutdown", "close", "disconnect"):
                method = getattr(service, method_name, None)
                if callable(method):
                    try:
                        result = method()
                        # Если метод async — await его
                        if hasattr(result, "__await__"):
                            await result
                        logger.info("Shutdown: %s.%s() — OK", name, method_name)
                    except Exception as e:
                        logger.error("Shutdown: %s.%s() — ошибка: %s", name, method_name, e)
                    break  # только один метод на сервис

        self._services.clear()
        self._factories.clear()
        self._shutdown_order.clear()
