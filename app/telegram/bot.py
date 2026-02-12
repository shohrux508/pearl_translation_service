from aiogram import Bot, Dispatcher
from app.config import settings
from app.container import Container
from app.telegram.routers import example

async def start_telegram(container: Container):
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    # Inject dependency into routers
    example.setup_router(container)

    # Include routers
    dp.include_router(example.router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
