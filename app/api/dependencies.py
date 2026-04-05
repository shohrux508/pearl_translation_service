"""
FastAPI-зависимости для инъекции сервисов через Depends().

Использование в роутерах:
    from app.api.dependencies import get_container

    @router.get("/example")
    async def example(container: Container = Depends(get_container)):
        service = container.gemini_service
"""

from fastapi import Request

from app.container import Container


def get_container(request: Request) -> Container:
    """Извлекает DI-контейнер из FastAPI app.state."""
    return request.app.state.container
