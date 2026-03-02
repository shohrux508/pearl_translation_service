import os
from pathlib import Path
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from app.container import Container
from app.services.document_manager import doc_manager

router = Router()

class AddDocState(StatesGroup):
    waiting_for_id = State()
    waiting_for_name = State()
    waiting_for_emoji = State()
    waiting_for_fields = State()
    waiting_for_ru_template = State()
    waiting_for_en_template = State()

def setup_router(container: Container):
    pass

@router.message(Command("add_doc"))
async def cmd_add_doc(message: types.Message, state: FSMContext):
    """
    Начинает процесс добавления нового типа документа.
    """
    await message.reply(
        "🛠 **Добавление нового типа документа**\n\n"
        "Шаг 1. Введите уникальный ID документа на английском (например: `marriage_cert`, `driver_license`).\n"
        "Без пробелов:",
        parse_mode="Markdown"
    )
    await state.set_state(AddDocState.waiting_for_id)

@router.message(AddDocState.waiting_for_id)
async def process_doc_id(message: types.Message, state: FSMContext):
    doc_id = message.text.strip().lower()
    await state.update_data(doc_id=doc_id)
    
    await message.reply(
        f"✅ ID `{doc_id}` принят.\n\n"
        "Шаг 2. Введите понятное название документа (например: `Свидетельство о браке`):",
        parse_mode="Markdown"
    )
    await state.set_state(AddDocState.waiting_for_name)

@router.message(AddDocState.waiting_for_name)
async def process_doc_name(message: types.Message, state: FSMContext):
    doc_name = message.text.strip()
    await state.update_data(doc_name=doc_name)
    
    await message.reply(
        f"✅ Название `{doc_name}` принято.\n\n"
        "Шаг 3. Отправьте 1 эмодзи для кнопки (например: 💍 или 📄):",
        parse_mode="Markdown"
    )
    await state.set_state(AddDocState.waiting_for_emoji)

@router.message(AddDocState.waiting_for_emoji)
async def process_doc_emoji(message: types.Message, state: FSMContext):
    emoji = message.text.strip()
    await state.update_data(emoji=emoji)
    
    await message.reply(
        f"✅ Эмодзи {emoji} принят.\n\n"
        "Шаг 4. Укажите поля для извлечения. Каждое поле с новой строки в формате:\n"
        "`ключ=Название на русском=Name in English`\n\n"
        "Пример:\n"
        "`husband_name=ФИО Мужа=Husband Name`\n"
        "`wife_name=ФИО Жены=Wife Name`\n"
        "`reg_date=Дата регистрации=Date of Registration`",
        parse_mode="Markdown"
    )
    await state.set_state(AddDocState.waiting_for_fields)

@router.message(AddDocState.waiting_for_fields)
async def process_doc_fields(message: types.Message, state: FSMContext):
    lines = message.text.strip().split("\n")
    
    prompt_fields_list = []
    ru_translations = {}
    en_translations = {}
    
    try:
        for line in lines:
            line = line.strip()
            if not line: continue
            
            parts = [p.strip() for p in line.split("=")]
            if len(parts) == 3:
                key, ru_name, en_name = parts
            elif len(parts) == 2:
                key, ru_name = parts
                en_name = ru_name
            else:
                key = parts[0]
                ru_name = key
                en_name = key
                
            prompt_fields_list.append(key)
            ru_translations[key] = ru_name
            en_translations[key] = en_name
            
        prompt_fields_str = ", ".join(prompt_fields_list)
        
        await state.update_data(
            prompt_fields=prompt_fields_str,
            ru_translations=ru_translations,
            en_translations=en_translations
        )
        
        await message.reply(
            f"✅ Поля успешно обработаны ({len(prompt_fields_list)} шт).\n\n"
            "Шаг 5. Отправьте готовый шаблон перевода для **РУССКОГО** языка (файл `.docx`).\n"
            "(Или отправьте слово `skip` чтобы пропустить и создать пустой шаблон).",
            parse_mode="Markdown"
        )
        await state.set_state(AddDocState.waiting_for_ru_template)
        
    except Exception as e:
        await message.reply(f"❌ Ошибка разбора полей. Убедитесь, что формат правильный.\nОшибка: {e}")

@router.message(AddDocState.waiting_for_ru_template, F.document | F.text)
async def process_ru_template(message: types.Message, state: FSMContext):
    data = await state.get_data()
    doc_id = data.get("doc_id")
    template_name = f"{doc_id.upper()}_TEMPLATE_RU.docx"
    save_path = Path("templates") / template_name
    save_path.parent.mkdir(exist_ok=True)
    
    if message.document and message.document.file_name.endswith('.docx'):
        await message.bot.download(message.document, destination=save_path)
        await message.reply("✅ Русский шаблон сохранён!")
    elif message.text and message.text.lower() == 'skip':
        pass # Skip saving, will be generated dynamically later if missing
    else:
        await message.reply("Пожалуйста, отправьте файл .docx или слово `skip`.")
        return

    await message.reply(
        "Шаг 6. Теперь отправьте шаблон перевода для **АНГЛИЙСКОГО** языка (файл `.docx`).\n"
        "(Или отправьте слово `skip` чтобы пропустить).",
        parse_mode="Markdown"
    )
    await state.set_state(AddDocState.waiting_for_en_template)

@router.message(AddDocState.waiting_for_en_template, F.document | F.text)
async def process_en_template(message: types.Message, state: FSMContext):
    data = await state.get_data()
    doc_id = data.get("doc_id")
    template_name = f"{doc_id.upper()}_TEMPLATE_EN.docx"
    save_path = Path("templates") / template_name
    save_path.parent.mkdir(exist_ok=True)
    
    if message.document and message.document.file_name.endswith('.docx'):
        await message.bot.download(message.document, destination=save_path)
    elif message.text and message.text.lower() == 'skip':
        pass
    else:
        await message.reply("Пожалуйста, отправьте файл .docx или слово `skip`.")
        return
        
    # Сохраняем все данные в базу (JSON)
    doc_manager.add_document_type(
        doc_id=data["doc_id"],
        name=data["doc_name"],
        emoji=data["emoji"],
        prompt_fields=data["prompt_fields"],
        ru_translations=data["ru_translations"],
        en_translations=data["en_translations"]
    )
    
    await state.clear()
    
    # Reload config to apply changes
    doc_manager.reload()
    
    await message.reply(
        f"🎉 **Готово!**\n\n"
        f"Новый документ `{data['doc_name']}` успешно добавлен в систему.\n"
        f"Вы можете проверить его, отправив фотографию в бот!",
        parse_mode="Markdown"
    )
