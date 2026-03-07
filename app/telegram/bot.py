from aiogram import Bot, Dispatcher
from app.config import settings
from app.container import Container
from app.telegram.routers import translator, admin_docs, admin_manage

async def start_telegram(container: Container):
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    # Inject dependency into routers
    translator.setup_router(container)
    admin_docs.setup_router(container)
    admin_manage.setup_router(container)

    # Include routers
    dp.include_router(translator.router)
    dp.include_router(admin_docs.router)
    dp.include_router(admin_manage.router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
