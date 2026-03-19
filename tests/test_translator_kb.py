from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from app.telegram.keyboards.translator_kb import (
    get_start_keyboard,
    get_flash_pro_keyboard,
    get_language_keyboard,
    get_retry_photo_keyboard,
    get_validation_keyboard,
    get_table_view_keyboard
)

def test_get_start_keyboard():
    kb = get_start_keyboard()
    assert isinstance(kb, ReplyKeyboardMarkup)
    assert len(kb.keyboard) >= 3
    assert "Перевод документа" in kb.keyboard[0][0].text

def test_get_flash_pro_keyboard():
    kb = get_flash_pro_keyboard()
    assert isinstance(kb, InlineKeyboardMarkup)
    assert len(kb.inline_keyboard) == 2

def test_get_language_keyboard():
    kb = get_language_keyboard()
    assert isinstance(kb, InlineKeyboardMarkup)
    assert len(kb.inline_keyboard) == 2

def test_get_retry_photo_keyboard():
    kb = get_retry_photo_keyboard()
    assert isinstance(kb, InlineKeyboardMarkup)
    assert len(kb.inline_keyboard) == 1

def test_get_validation_keyboard_flat():
    data = {"name": "Test"}
    kb = get_validation_keyboard(data, lang_code="ru")
    assert isinstance(kb, InlineKeyboardMarkup)
    buttons_flat = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    assert "editf_name" in buttons_flat
    assert "confirm_generation" in buttons_flat

def test_get_validation_keyboard_schema():
    data = {
        "fields": {"name": "Test"},
        "tables": {"items": [{"a": "1"}]}
    }
    kb = get_validation_keyboard(data, lang_code="en")
    assert isinstance(kb, InlineKeyboardMarkup)
    buttons_flat = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    assert "raw_json_mode" in buttons_flat
    assert "editf_name" in buttons_flat
    assert "viewt_items_0" in buttons_flat
    assert "confirm_generation" in buttons_flat

def test_get_table_view_keyboard():
    kb = get_table_view_keyboard("items", page=0, total_pages=2, start_idx=0, end_idx=5, lang_code="en")
    buttons_flat = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    assert "viewt_items_1" in buttons_flat # Next page button
    assert "back_to_validation" in buttons_flat
    assert "editt_items_0" in buttons_flat
