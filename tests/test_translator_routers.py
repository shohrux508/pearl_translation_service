import pytest
from unittest.mock import AsyncMock
from app.telegram.routers.translator import cmd_start, menu_translate
from app.telegram.states.translator_states import TranslationState

@pytest.mark.asyncio
async def test_cmd_start():
    message = AsyncMock()
    state = AsyncMock()
    
    await cmd_start(message=message, state=state)
    
    state.clear.assert_awaited_once()
    message.answer.assert_awaited_once()
    
    args, kwargs = message.answer.call_args
    assert "Pearl" in args[0]
    assert kwargs.get("reply_markup") is not None

@pytest.mark.asyncio
async def test_menu_translate():
    message = AsyncMock()
    state = AsyncMock()
    
    await menu_translate(message=message, state=state)
    
    state.clear.assert_awaited_once()
    state.set_state.assert_awaited_once_with(TranslationState.waiting_for_photos)
    message.answer.assert_awaited_once()
    
    args, kwargs = message.answer.call_args
    assert "Сфотографируйте документ" in args[0]

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_cmd_start())
    asyncio.run(test_menu_translate())
    print("\n[SUCCESS] Custom runner passed all router tests!")
