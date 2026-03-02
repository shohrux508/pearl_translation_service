from aiogram import Router, types
from aiogram.filters import CommandStart
from app.container import Container

router = Router()
container: Container | None = None  # Will be injected

def setup_router(di_container: Container):
    global container
    container = di_container

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    if not container:
        await message.answer("Service not initialized")
        return

    example_service = container.get("example_service")
    msg = example_service.get_message()
    await message.answer(f"Bot says: {msg}")
