import asyncio
import logging
from app.config import settings
from app.container import Container
from app.services.gemini_service import GeminiTranslationService
from app.services.docx_service import DocxService
from app.services.file_manager_service import FileManagerService

logger = logging.getLogger(__name__)

class App:
    def __init__(self):
        self.container = Container()

    def setup_services(self):
        logger.info("Setting up services...")
        
        # Регистрируем наш сервис (если токена нет, кинет ValueError при первом использовании или сейчас)
        if settings.GEMINI_API_KEY:
            self.container.register("gemini_service", GeminiTranslationService(api_key=settings.GEMINI_API_KEY))
        else:
            logger.warning("GEMINI_API_KEY не установлен, gemini_service не зарегистрирован.")
            
        # Регистрируем инфраструктурные сервисы
        self.container.register("docx_service", DocxService())
        self.container.register("file_manager", FileManagerService(temp_dir="temp"))

    async def setup_telegram(self):
        if settings.RUN_TELEGRAM:
            from app.telegram.bot import start_telegram
            logger.info("Starting Telegram Bot...")
            return start_telegram(self.container)
        return None

    async def setup_api(self):
        if settings.RUN_API:
            from app.api.server import start_api
            logger.info("Starting API Server...")
            return start_api(self.container)
        return None

    async def run(self):
        self.setup_services()
        
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

        await asyncio.gather(*tasks)
