import pytest
from aiogram.types import Message, User, Chat
from app.config import settings
from app.telegram.filters import IsAdmin
from datetime import datetime

@pytest.mark.asyncio
async def test_is_admin_filter():
    filter_obj = IsAdmin()

    # Mock settings
    settings.ADMIN_IDS = "123, 456"

    # Mock message
    msg = Message(
        message_id=1,
        date=datetime.now(),
        chat=Chat(id=1, type="private"),
        from_user=User(id=123, is_bot=False, first_name="Test")
    )

    assert await filter_obj(msg) == True

    msg2 = Message(
        message_id=2,
        date=datetime.now(),
        chat=Chat(id=1, type="private"),
        from_user=User(id=999, is_bot=False, first_name="Test")
    )
    assert await filter_obj(msg2) == False

    # Empty settings
    settings.ADMIN_IDS = ""
    assert await filter_obj(msg) == False
