from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from app.services.document_manager import doc_manager

def get_start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📄 Перевод документа")],
            [KeyboardButton(text="🗂 Мои шаблоны"), KeyboardButton(text="➕ Добавить шаблон")],
            [KeyboardButton(text="❓ Как это работает?")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие ниже"
    )

def get_flash_pro_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Быстрое распознавание (Flash)", callback_data="start_recog_flash")],
        [InlineKeyboardButton(text="🧠 Точное распознавание (Pro)", callback_data="start_recog_pro")]
    ])

def get_doc_types_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    doc_types = doc_manager.get_types()
    for doc_id, doc_info in doc_types.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{doc_info['emoji']} {doc_info['name']}", 
                callback_data=f"doctype_{doc_id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский язык", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 Английский язык", callback_data="lang_en")]
    ])

def get_retry_photo_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Отправить новое фото", callback_data="retry_photo")]
    ])

def get_validation_keyboard(data_dict: dict, lang_code: str = "ru") -> InlineKeyboardMarkup:
    buttons = []
    
    # Check if this is the new schema format (has fields, tables, etc) or flat format
    has_schema = "fields" in data_dict or "tables" in data_dict
    
    if has_schema:
        fields = data_dict.get("fields", {})
        tables = data_dict.get("tables", {})
        
        # Add basic fields as editable buttons
        current_row = []
        for key in fields.keys():
            localized_name = doc_manager.localize_field(key, lang_code)
            btn_text = f"✏️ {localized_name[:20]}"
            cb_data = f"editf_{key}"
            if len(cb_data) > 64: cb_data = cb_data[:64]
            current_row.append(InlineKeyboardButton(text=btn_text, callback_data=cb_data))
            if len(current_row) == 2:
                buttons.append(current_row)
                current_row = []
        if current_row:
            buttons.append(current_row)
            
        # Add table buttons
        for table_key in tables.keys():
            localized_name = doc_manager.localize_field(table_key, lang_code)
            btn_text = f"📊 Редактировать {localized_name[:15]}" if lang_code == "ru" else f"📊 Edit {localized_name[:15]}"
            cb_data = f"viewt_{table_key}_0"
            if len(cb_data) > 64: cb_data = cb_data[:64]
            buttons.append([InlineKeyboardButton(text=btn_text, callback_data=cb_data)])
            
        # Raw JSON mode
        raw_text = "⚙️ Проверить сырые данные (JSON)" if lang_code == "ru" else "⚙️ Check raw data (JSON)"
        buttons.append([InlineKeyboardButton(text=raw_text, callback_data="raw_json_mode")])
        
    else:
        # Legacy flat mapping
        current_row = []
        for key in data_dict.keys():
            localized_name = doc_manager.localize_field(key, lang_code)
            btn_text = f"✏️ {localized_name[:20]}"
            cb_data = f"editf_{key}"
            if len(cb_data) > 64: cb_data = cb_data[:64]
            current_row.append(InlineKeyboardButton(text=btn_text, callback_data=cb_data))
            if len(current_row) == 2:
                buttons.append(current_row)
                current_row = []
        if current_row:
            buttons.append(current_row)
    
    confirm_text = "✅ Подтвердить и создать" if lang_code == "ru" else "✅ Confirm and generate"
    buttons.append([InlineKeyboardButton(text=confirm_text, callback_data="confirm_generation")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_table_view_keyboard(table_key: str, page: int, total_pages: int, start_idx: int, end_idx: int, lang_code: str) -> InlineKeyboardMarkup:
    buttons = []
    
    for i in range(start_idx, end_idx):
        btn_text = f"✏️ Строка {i+1}" if lang_code == "ru" else f"✏️ Row {i+1}"
        
        cb_data = f"editt_{table_key}_{i}"
        if len(cb_data) > 64: cb_data = cb_data[:64]
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=cb_data)])
        
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"viewt_{table_key}_{page-1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"viewt_{table_key}_{page+1}"))
    
    if nav_row:
        buttons.append(nav_row)
        
    back_text = "🔙 Вернуться к сводке" if lang_code == "ru" else "🔙 Back to summary"
    buttons.append([InlineKeyboardButton(text=back_text, callback_data="back_to_validation")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
