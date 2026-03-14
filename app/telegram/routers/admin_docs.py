import os
from pathlib import Path
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from app.container import Container
from app.services.document_manager import doc_manager

router = Router()

import re
import uuid

def generate_doc_id(name: str) -> str:
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 'ж': 'zh',
        'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
        'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts',
        'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu',
        'я': 'ya'
    }
    result = []
    for char in name.lower():
        if char in translit_map:
            result.append(translit_map[char])
        elif char.isalnum():
            result.append(char)
        elif char in ' -':
            result.append('_')
    id_str = re.sub(r'_+', '_', ''.join(result)).strip('_')
    if not id_str:
        id_str = f"doc_{str(uuid.uuid4())[:8]}"
    return id_str

class AddDocState(StatesGroup):
    waiting_for_photos = State()
    waiting_for_field_edit_choice = State()
    editing_fields_raw = State()
    waiting_for_new_title = State()
    waiting_for_emoji = State()
    waiting_for_ru_template = State()
    waiting_for_en_template = State()

gemini_service = None
file_manager = None

def setup_router(container: Container):
    global gemini_service, file_manager
    try:
        gemini_service = container.get("gemini_service")
        file_manager = container.get("file_manager")
    except ValueError:
        pass

@router.message(F.text == "➕ Добавить шаблон")
async def cmd_add_doc(message: types.Message, state: FSMContext):
    """
    Начинает процесс добавления нового шаблона.
    """
    await message.reply(
        "🛠 **Добавление нового шаблона**\n\n"
        "Шаг 1. Сфотографируйте документ, из которого мы будем делать шаблон.\n"
        "Я автоматически определю его тип, извлеку все нужные поля, переведу их и сгенерирую ключи.\n"
        "Вы можете отправить несколько страниц.\n\n"
        "📸 Пожалуйста, отправьте фото документа:",
        parse_mode="Markdown"
    )
    await state.update_data(file_ids=[])
    await state.set_state(AddDocState.waiting_for_photos)

@router.message(F.photo, AddDocState.waiting_for_photos)
async def handle_document_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    file_ids = data.get("file_ids", [])
    
    photo = message.photo[-1]
    file_ids.append(photo.file_id)
    await state.update_data(file_ids=file_ids)
    
    total_pages = len(file_ids)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Быстрый анализ (Flash)", callback_data="admin_analyze_template_flash")],
        [InlineKeyboardButton(text="🧠 Глубокий анализ (Pro)", callback_data="admin_analyze_template_pro")]
    ])
    
    text = f"📄 Загружено страниц: **{total_pages}**\nОтправьте еще фото, либо нажмите кнопку ниже для запуска анализа:"
    
    last_msg_id = data.get("last_tracking_msg_id")
    if last_msg_id:
        try:
            await message.bot.edit_message_text(chat_id=message.chat.id, message_id=last_msg_id, text=text, reply_markup=keyboard, parse_mode="Markdown")
        except Exception:
            msg = await message.reply(text, reply_markup=keyboard, parse_mode="Markdown")
            await state.update_data(last_tracking_msg_id=msg.message_id)
    else:
        msg = await message.reply(text, reply_markup=keyboard, parse_mode="Markdown")
        await state.update_data(last_tracking_msg_id=msg.message_id)

@router.callback_query(F.data.startswith("admin_analyze_template_"), AddDocState.waiting_for_photos)
async def analyze_template(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    file_ids = data.get("file_ids", [])
    
    if not file_ids:
        await callback.message.answer("❌ Ошибка: фото не найдены. Отправьте фото заново.")
        return
        
    use_pro = callback.data.endswith("_pro")
    model_name = "Pro" if use_pro else "Flash"
    processing_msg = await callback.message.edit_text(f"⏳ Анализирую структуру документа (модель: {model_name}). Это может занять секунд 10-25...")
    
    if not gemini_service or not file_manager:
        await processing_msg.edit_text("❌ Ошибка: Сервисы не настроены. Обратитесь к администратору.")
        return
        
    photo_paths = []
    try:
        photo_paths = await file_manager.download_photos(callback.bot, callback.from_user.id, file_ids)
        result = await gemini_service.analyze_document_for_template(photo_paths, use_pro=use_pro)
        
        doc_name = result.get("doc_name", "Новый документ")
        doc_id = generate_doc_id(doc_name)
        
        prompt_fields_list = []
        ru_translations = {}
        en_translations = {}
        
        fields = result.get("fields", [])
        for field in fields:
            key = field.get("keyword")
            if key:
                prompt_fields_list.append(key)
                ru_translations[key] = field.get("ru_name", key)
                en_translations[key] = field.get("en_name", key)
                
        prompt_fields_str = ", ".join(prompt_fields_list)
        
        await state.update_data(
            doc_name=doc_name,
            doc_id=doc_id,
            prompt_fields=prompt_fields_str,
            ru_translations=ru_translations,
            en_translations=en_translations
        )
        
        result_text_intro = f"✅ Авто-определение успешно!\n\n📄 **Название:** `{doc_name}` (ID: `{doc_id}`)\n📋 **Найдено полей ({len(prompt_fields_list)}):**\n\n"
        
        # Разделяем длинный список на несколько сообщений (длина сообщения в Telegram ~4096 символов)
        MAX_MESSAGE_LENGTH = 3800
        current_message_text = result_text_intro
        messages_to_send = []
        
        for key in prompt_fields_list:
            line = f"• `{key}`\n"
            if len(current_message_text) + len(line) > MAX_MESSAGE_LENGTH:
                messages_to_send.append(current_message_text)
                current_message_text = ""
            current_message_text += line
            
        current_message_text += "\nВсе ли поля определены верно?"
        messages_to_send.append(current_message_text)
        
        # Отправляем первое сообщение редактированием
        await processing_msg.edit_text(messages_to_send[0], parse_mode="Markdown")
        
        # Отправляем остальные части отдельными сообщениями, если список был очень большой
        for i, m in enumerate(messages_to_send[1:]):
            if i == len(messages_to_send[1:]) - 1:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Всё верно, продолжить", callback_data="admin_confirm_fields")],
                    [InlineKeyboardButton(text="✏️ Поправить поля", callback_data="admin_edit_fields")],
                    [InlineKeyboardButton(text="🏷 Изменить название", callback_data="admin_edit_title")]
                ])
                await callback.message.answer(m, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await callback.message.answer(m, parse_mode="Markdown")
             
        if len(messages_to_send) == 1:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Всё верно, продолжить", callback_data="admin_confirm_fields")],
                [InlineKeyboardButton(text="✏️ Поправить поля", callback_data="admin_edit_fields")],
                [InlineKeyboardButton(text="🏷 Изменить название", callback_data="admin_edit_title")]
            ])
            await processing_msg.edit_reply_markup(reply_markup=keyboard)
             
        await state.set_state(AddDocState.waiting_for_field_edit_choice)
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Произошла ошибка при анализе ИИ:\n{str(e)}\n\nПопробуйте отправить другие, более четкие фото или добавьте шаблон заново.")
    finally:
        if file_manager and photo_paths:
            file_manager.cleanup_files(photo_paths)

@router.callback_query(F.data == "admin_confirm_fields", AddDocState.waiting_for_field_edit_choice)
async def confirm_fields(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    
    await callback.message.answer(
        "Шаг 2. Отправьте 1 эмодзи для кнопки (например: 💍 или 📄):",
        parse_mode="Markdown"
    )
    await state.set_state(AddDocState.waiting_for_emoji)

@router.callback_query(F.data == "admin_edit_fields", AddDocState.waiting_for_field_edit_choice)
async def edit_fields(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    
    prompt_fields_list = data.get("prompt_fields", "").split(", ")
    ru_translations = data.get("ru_translations", {})
    
    lines = []
    for key in prompt_fields_list:
        if key.strip():
            ru_name = ru_translations.get(key, key)
            lines.append(f"{key}: {ru_name}")
            
    text_to_edit = "\n".join(lines)
    
    msg = (
        "✏️ **Редактирование полей**\n\n"
        "Скопируйте текст ниже, удалите лишние строки, поменяйте названия или добавьте новые с новой строки "
        "(ключи для новых генерировать не нужно, просто напишите русское название).\n"
        "Затем отправьте исправленный текст мне обратно.\n\n"
        f"```text\n{text_to_edit}\n```"
    )
    
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(msg, parse_mode="Markdown")
    await state.set_state(AddDocState.editing_fields_raw)

@router.callback_query(F.data == "admin_edit_title", AddDocState.waiting_for_field_edit_choice)
async def edit_title(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    doc_name = data.get("doc_name")
    
    msg = (
        f"🏷 **Изменение названия**\n\n"
        f"Текущее название: `{doc_name}`\n"
        "Отправьте новое название для этого шаблона ответным сообщением."
    )
    
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(msg, parse_mode="Markdown")
    await state.set_state(AddDocState.waiting_for_new_title)

@router.message(AddDocState.waiting_for_new_title, F.text)
async def process_new_title(message: types.Message, state: FSMContext):
    new_title = message.text.strip()
    await state.update_data(doc_name=new_title, doc_id=generate_doc_id(new_title))
    
    data = await state.get_data()
    prompt_fields_str = data.get("prompt_fields", "")
    prompt_fields_list = prompt_fields_str.split(", ") if prompt_fields_str else []
    ru_translations = data.get("ru_translations", {})
    doc_id = data.get("doc_id")
    
    result_text_intro = f"✅ Название обновлено!\n\n📄 **Название:** `{new_title}` (ID: `{doc_id}`)\n📋 **Итого полей ({len(prompt_fields_list)}):**\n\n"
    
    MAX_MESSAGE_LENGTH = 3800
    current_message_text = result_text_intro
    messages_to_send = []
    
    for key in prompt_fields_list:
        if not key.strip():
            continue
        ru_name = ru_translations.get(key, key)
        line = f"• `{key}` (RU: {ru_name})\n"
        if len(current_message_text) + len(line) > MAX_MESSAGE_LENGTH:
            messages_to_send.append(current_message_text)
            current_message_text = ""
        current_message_text += line
        
    current_message_text += "\nВсё ли теперь верно?"
    messages_to_send.append(current_message_text)
    
    for i, m in enumerate(messages_to_send):
        if i == len(messages_to_send) - 1:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Всё верно, продолжить", callback_data="admin_confirm_fields")],
                [InlineKeyboardButton(text="✏️ Поправить поля", callback_data="admin_edit_fields")],
                [InlineKeyboardButton(text="🏷 Изменить название", callback_data="admin_edit_title")]
            ])
            await message.answer(m, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.answer(m, parse_mode="Markdown")
            
    await state.set_state(AddDocState.waiting_for_field_edit_choice)

@router.message(AddDocState.editing_fields_raw)
async def process_edited_fields(message: types.Message, state: FSMContext):
    data = await state.get_data()
    ru_translations = data.get("ru_translations", {})
    en_translations = data.get("en_translations", {})
    
    lines = message.text.strip().split("\n")
    
    new_prompt_fields_list = []
    new_ru_translations = {}
    new_en_translations = {}
    
    fields_to_generate = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip()
            ru_name = parts[1].strip()
            new_prompt_fields_list.append(key)
            new_ru_translations[key] = ru_name
            # Keep old english translation if exists
            new_en_translations[key] = en_translations.get(key, key)
        else:
            # Just a russian name, needs generation
            fields_to_generate.append(line)
            
    if fields_to_generate:
        processing_msg = await message.reply("⏳ Генерирую ключи для новых полей...")
        try:
            generated_fields = await gemini_service.generate_field_translations(fields_to_generate)
            for item in generated_fields:
                if isinstance(item, dict) and "keyword" in item and "ru_name" in item and "en_name" in item:
                    key = item["keyword"]
                    new_prompt_fields_list.append(key)
                    new_ru_translations[key] = item["ru_name"]
                    new_en_translations[key] = item["en_name"]
            await processing_msg.delete()
        except Exception as e:
            await processing_msg.edit_text(f"❌ Ошибка генерации новых полей: {e}")
            return
            
    prompt_fields_str = ", ".join(new_prompt_fields_list)
    await state.update_data(
        prompt_fields=prompt_fields_str,
        ru_translations=new_ru_translations,
        en_translations=new_en_translations
    )
    
    # Show updated list
    doc_name = data.get("doc_name")
    doc_id = data.get("doc_id")
    result_text_intro = f"✅ Список полей обновлен!\n\n📄 **Название:** `{doc_name}` (ID: `{doc_id}`)\n📋 **Итого полей ({len(new_prompt_fields_list)}):**\n\n"
    
    MAX_MESSAGE_LENGTH = 3800
    current_message_text = result_text_intro
    messages_to_send = []
    
    for key in new_prompt_fields_list:
        line = f"• `{key}` (RU: {new_ru_translations[key]})\n"
        if len(current_message_text) + len(line) > MAX_MESSAGE_LENGTH:
            messages_to_send.append(current_message_text)
            current_message_text = ""
        current_message_text += line
        
    current_message_text += "\nВсе ли поля теперь верны?"
    messages_to_send.append(current_message_text)
    
    for i, m in enumerate(messages_to_send):
        if i == len(messages_to_send) - 1:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Всё верно, продолжить", callback_data="admin_confirm_fields")],
                [InlineKeyboardButton(text="✏️ Поправить поля", callback_data="admin_edit_fields")],
                [InlineKeyboardButton(text="🏷 Изменить название", callback_data="admin_edit_title")]
            ])
            await message.answer(m, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.answer(m, parse_mode="Markdown")
            
    await state.set_state(AddDocState.waiting_for_field_edit_choice)

@router.message(AddDocState.waiting_for_emoji)
async def process_doc_emoji(message: types.Message, state: FSMContext):
    emoji = message.text.strip()
    await state.update_data(emoji=emoji)
    
    await message.reply(
        f"✅ Эмодзи {emoji} принят.\n\n"
        "Шаг 3. Отправьте готовый шаблон перевода для **РУССКОГО** языка (файл `.docx`).\n"
        "(Или отправьте слово `skip` чтобы пропустить и создать пустой шаблон).",
        parse_mode="Markdown"
    )
    await state.set_state(AddDocState.waiting_for_ru_template)

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
        "Шаг 4. Теперь отправьте шаблон перевода для **АНГЛИЙСКОГО** языка (файл `.docx`).\n"
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
        
    config = {"fields": {}}
    for key, ru_val in data["ru_translations"].items():
        config["fields"][key] = {
            "type": "string",
            "ui_mapping": {
                "ru": ru_val,
                "en": data["en_translations"].get(key, ru_val)
            }
        }

    # Сохраняем все данные в базу (JSON)
    doc_manager.add_document_type(
        doc_id=data["doc_id"],
        name=data["doc_name"],
        emoji=data["emoji"],
        config=config
    )
    
    await state.clear()
    
    # Reload config to apply changes
    doc_manager.reload()
    
    await message.reply(
        f"🎉 **Готово!**\n\n"
        f"Новый шаблон `{data['doc_name']}` успешно добавлен в систему.\n"
        f"Вы можете проверить его, отправив фотографию в бот!",
        parse_mode="Markdown"
    )
