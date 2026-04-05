"""
Глобальные фикстуры для pytest.
"""

import pytest
from unittest.mock import MagicMock

from app.container import Container


@pytest.fixture
def container() -> Container:
    """Чистый DI-контейнер для тестов."""
    return Container()


@pytest.fixture
def mock_gemini_service():
    """Мок GeminiTranslationService без реальных API-вызовов."""
    import google.generativeai as genai
    genai.configure = MagicMock()
    genai.GenerativeModel = MagicMock()

    from app.services.gemini_service import GeminiTranslationService
    return GeminiTranslationService(api_key="test_api_key")


@pytest.fixture
def container_with_services(container: Container, mock_gemini_service) -> Container:
    """Контейнер с зарегистрированными мок-сервисами."""
    from app.services.docx_service import DocxService
    from app.services.file_manager_service import FileManagerService

    container.register("gemini_service", mock_gemini_service)
    container.register("docx_service", DocxService())
    container.register("file_manager", FileManagerService(temp_dir="temp"))
    return container
