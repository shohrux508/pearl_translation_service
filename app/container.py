from typing import Any, Dict

class Container:
    def __init__(self):
        self._services: Dict[str, Any] = {}

    def register(self, name: str, instance: Any) -> None:
        if name in self._services:
            raise ValueError(f"Service '{name}' already registered")
        self._services[name] = instance

    def get(self, name: str) -> Any:
        if name not in self._services:
            raise ValueError(f"Service '{name}' not found")
        return self._services[name]
