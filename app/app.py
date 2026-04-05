"""
Orchestrator — сборка и запуск приложения.

Отвечает за:
1. Настройку логирования
2. Регистрацию сервисов (включая lazy init)
3. Запуск Telegram-бота и/или API
4. Graceful shutdown
"""

import asyncio
import logging

from app.config import settings
from app.container import Container

logger = logging.getLogger(__name__)


class App:
    def __init__(self) -> None:
        self.container = Container()

    # ── Setup ─────────────────────────────────────────────────────────

    def setup_logging(self) -> None:
        """Настраивает Loguru как единый логгер (перехватывает stdlib logging)."""
        from libs.utils.logger import setup_logger

        setup_logger(
            level=settings.LOG_LEVEL,
            log_file=settings.LOG_FILE,
            json_mode=settings.LOG_JSON,
        )

    def setup_services(self) -> None:
        """Регистрация бизнес-сервисов."""
        logger.info("Setting up services...")

        from app.services.docx_service import DocxService
        from app.services.file_manager_service import FileManagerService

        # Gemini — lazy init (тяжёлый клиент, создаётся при первом обращении)
        if settings.GEMINI_API_KEY:
            def _create_gemini():
                from app.services.gemini_service import GeminiTranslationService
                return GeminiTranslationService(api_key=settings.GEMINI_API_KEY)

            self.container.register_lazy("gemini_service", _create_gemini)
        else:
            logger.warning("GEMINI_API_KEY не установлен, gemini_service не зарегистрирован.")

        # Инфраструктурные сервисы (лёгкие, регистрируем сразу)
        self.container.register("docx_service", DocxService())
        self.container.register("file_manager", FileManagerService(temp_dir="temp"))

    # ── Component runners ─────────────────────────────────────────────

    async def setup_telegram(self) -> asyncio.Task | None:
        if settings.RUN_TELEGRAM:
            from app.telegram.bot import start_telegram

            logger.info("Starting Telegram Bot...")
            return start_telegram(self.container)
        return None

    async def setup_api(self) -> asyncio.Task | None:
        if settings.RUN_API:
            from app.api.server import start_api

            logger.info("Starting API Server...")
            return start_api(self.container)
        return None

    # ── Main loop ─────────────────────────────────────────────────────

    async def run(self) -> None:
        # 1. Логирование — первым делом
        self.setup_logging()

        # 2. Сервисы
        self.setup_services()

        # 3. Компоненты
        tasks = []

        telegram_task = await self.setup_telegram()
        if telegram_task:
            tasks.append(telegram_task)

        api_task = await self.setup_api()
        if api_task:
            tasks.append(api_task)

        if not tasks:
            logger.warning("No components enabled to run (RUN_TELEGRAM=False, RUN_API=False)")
            return

        try:
            await asyncio.gather(*tasks)
        finally:
            # 4. Graceful shutdown
            logger.info("Shutting down services...")
            await self.container.shutdown()
            logger.info("All services stopped.")
