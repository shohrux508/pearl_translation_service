from app.services.document_manager import doc_manager

START_GREETING = (
    "👋 **Pearl — перевод документов с помощью AI**\n\n"
    "Что вы хотите сделать?"
)

PHOTO_INSTRUCTION_TEXT = (
    "📷 **Сфотографируйте документ**\n\n"
    "Советы для лучшего распознавания:\n"
    "• хороший свет\n"
    "• весь документ в кадре\n"
    "• без бликов"
)

HELP_TEXT = (
    "❓ **Как это работает**\n\n"
    "1️⃣ Отправьте фото документа (или нескольких страниц)\n"
    "2️⃣ Проверьте распознанные поля и отредактируйте их при необходимости\n"
    "3️⃣ Получите готовый перевод в формате Word"
)

ERROR_MSG_RECOGNITION = (
    "⚠️ Не удалось распознать документ\n\n"
    "Причины:\n"
    "• плохое освещение\n"
    "• размытое фото\n"
    "• часть документа не попала в кадр\n\n"
    "Попробуйте отправить фото снова."
)

def get_validation_text(data_dict: dict, lang_name: str = "выбранный", lang_code: str = "ru") -> str:
    title = f"🤖 **Результат распознавания ({lang_name}):**\n" if lang_code == "ru" else f"🤖 **Extraction Result ({lang_name}):**\n"
    lines = [title]
    has_schema = "fields" in data_dict or "tables" in data_dict
    
    if has_schema:
        metadata = data_dict.get("metadata", {})
        fields = data_dict.get("fields", {})
        tables = data_dict.get("tables", {})
        
        lines.append("📌 **Все извлеченные данные:**" if lang_code == "ru" else "📌 **All extracted data:**")
        for k, v in fields.items():
            localized_name = doc_manager.localize_field(k, lang_code)
            lines.append(f"▪️ **{localized_name}**: `{v}`")
            
        for tk, tv in tables.items():
            if isinstance(tv, list):
                localized_name = doc_manager.localize_field(tk, lang_code)
                lines.append(f"📋 **{localized_name}**: распознано {len(tv)} строк" if lang_code == "ru" else f"📋 **{localized_name}**: {len(tv)} rows extracted")
                
        instr = "\n_Всё верно? Если нужно, отредактируйте данные ниже._" if lang_code == "ru" else "\n_Is everything correct? Edit data below if needed._"
    else:
        for k, v in data_dict.items():
            localized_name = doc_manager.localize_field(k, lang_code)
            lines.append(f"▪️ **{localized_name}**: `{v}`")
        instr = "\n_Нажмите на кнопку с именем поля ниже, если нужно его исправить._" if lang_code == "ru" else "\n_Click on the field name below if you need to manually fix it._"
        
    return "\n".join(lines) + "\n" + instr
