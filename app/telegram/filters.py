from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from app.config import settings

class IsAdmin(BaseFilter):
    async def __call__(self, obj: Message | CallbackQuery) -> bool:
        user_id = obj.from_user.id
        admin_ids = settings.parsed_admin_ids

        if not admin_ids:
            # If ADMIN_IDS is not configured, we should secure it by default to avoid vulnerability.
            return False

        return user_id in admin_ids
