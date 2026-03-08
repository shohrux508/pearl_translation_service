import asyncio
import logging
from pathlib import Path
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from app.container import Container
from app.services.document_manager import doc_manager

router = Router()
container_instance: Container = None

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

class TranslationState(StatesGroup):
    waiting_for_photos = State()
    choosing_doc_type = State()
    choosing_language = State()
    validating_data = State()
    editing_field = State()

def setup_router(container: Container):
    """Инжектим контейнер в роутер."""
    global container_instance
    container_instance = container

def get_service(name: str):
    """Безопасное получение сервиса из DI контейнера."""
    try:
        return container_instance.get(name)
    except (KeyError, AttributeError):
        return None

def get_gemini_service():
    """Безопасное получение сервиса Gemini (оставлено для совместимости)."""
    return get_service("gemini_service")

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📄 Перевести документ"), KeyboardButton(text="📁 Мои последние документы")],
            [KeyboardButton(text="❓ Как это работает"), KeyboardButton(text="🌐 Выбрать язык")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие ниже"
    )
    await message.answer(START_GREETING, reply_markup=keyboard, parse_mode="Markdown")

@router.message(F.text == "📄 Перевести документ")
async def menu_translate(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(TranslationState.waiting_for_photos)
    await message.answer(PHOTO_INSTRUCTION_TEXT, reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")

@router.message(F.text == "❓ Как это работает")
async def menu_help(message: types.Message):
    await message.answer(HELP_TEXT, parse_mode="Markdown")

@router.message(F.text.in_({"📁 Мои последние документы", "🌐 Выбрать язык"}))
async def menu_stub(message: types.Message):
    await message.answer("⏳ Эта функция находится в разработке", show_alert=True)

@router.callback_query(F.data == "retry_photo")
async def retry_photo_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await state.set_state(TranslationState.waiting_for_photos)
    await callback.message.edit_text(PHOTO_INSTRUCTION_TEXT, parse_mode="Markdown")

@router.message(F.photo, TranslationState.waiting_for_photos)
async def handle_document_photo(message: types.Message, state: FSMContext):
    """Принимает фотографии документа, накапливая их."""
    gemini_service = get_gemini_service()
    if not gemini_service:
        await message.reply("❌ Сервис перевода (Gemini) в данный момент недоступен. Проверьте API ключ.")
        return

    data = await state.get_data()
    file_ids = data.get("file_ids", [])
    
    photo = message.photo[-1]
    file_ids.append(photo.file_id)
    await state.update_data(file_ids=file_ids)
    
    total_pages = len(file_ids)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Начать распознавание", callback_data="start_recognition")]
    ])
    
    text = f"📄 Получено **{total_pages}** страниц документа\n\nМожете отправить еще фото, либо нажмите кнопку ниже для продолжения:"
    
    # Check if there is already a message tracking this grouped upload to edit it, or send a new one
    last_msg_id = data.get("last_tracking_msg_id")
    if last_msg_id:
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id, 
                message_id=last_msg_id, 
                text=text, 
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception:
             # Just send a new message if editing fails
             msg = await message.reply(text, reply_markup=keyboard, parse_mode="Markdown")
             await state.update_data(last_tracking_msg_id=msg.message_id)
    else:
        msg = await message.reply(text, reply_markup=keyboard, parse_mode="Markdown")
        await state.update_data(last_tracking_msg_id=msg.message_id)

@router.callback_query(F.data == "start_recognition", TranslationState.waiting_for_photos)
async def start_recognition_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    file_ids = data.get("file_ids", [])
    
    if not file_ids:
        await callback.message.answer("❌ Ошибка: фото не найдены. Отправьте фото заново.")
        return
        
    await ask_for_doc_type(callback.message, state, edit_message=True)

async def ask_for_doc_type(message: types.Message, state: FSMContext, edit_message: bool = False) -> None:
    """Отправляет или обновляет сообщение для выбора типа документа."""
    buttons = []
    doc_types = doc_manager.get_types()
    for doc_id, doc_info in doc_types.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{doc_info['emoji']} {doc_info['name']}", 
                callback_data=f"doctype_{doc_id}"
            )
        ])
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    text = "📸 Все фото получены!\nПожалуйста, выберите тип документа, чтобы мы могли правильно его перевести:"

    if edit_message:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await message.reply(text, reply_markup=keyboard)
        
    await state.set_state(TranslationState.choosing_doc_type)

@router.callback_query(F.data.startswith("doctype_"), TranslationState.choosing_doc_type)
async def process_document_type(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор типа документа и предлагает выбрать язык перевода."""
    doc_type = callback.data.replace("doctype_", "")
    await state.update_data(doc_type=doc_type)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский язык", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 Английский язык", callback_data="lang_en")]
    ])
    
    await callback.answer()
    await callback.message.edit_text(
        "✅ Тип документа выбран.\n\n🌐 Теперь, пожалуйста, выберите язык, на который нужно перевести данные:",
        reply_markup=keyboard
    )
    await state.set_state(TranslationState.choosing_language)

@router.callback_query(F.data.startswith("lang_"), TranslationState.choosing_language)
async def process_language(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор языка и запускает пайплайн распознавания и перевода."""
    lang = callback.data.replace("lang_", "")
    data = await state.get_data()
    doc_type = data.get("doc_type")
    file_ids = data.get("file_ids", [])
    await state.clear()
    
    if not file_ids or not doc_type:
        await callback.message.edit_text("❌ Ошибка: сессия устарела или данные не найдены. Пожалуйста, отправьте фото документа заново.")
        return

    lang_name = "Русский" if lang == "ru" else "Английский"
    current_config = doc_manager.get_document_config(doc_type, lang)
    if not current_config:
        await callback.answer("Неизвестный тип документа", show_alert=True)
        return

    await callback.answer()
    processing_msg = await callback.message.edit_text(
        f"✅ Документ: **{current_config['name']}**\n✅ Язык перевода: **{lang_name}**\n\n📸 Фото получено\n\n⏳ Обрабатываем документ...\n[1/3] Анализ изображения", 
        parse_mode="Markdown"
    )

    gemini_service = get_gemini_service()
    docx_service = get_service("docx_service")
    file_manager = get_service("file_manager")
    
    if not gemini_service or not docx_service or not file_manager:
        await processing_msg.edit_text("❌ Сервисы (Gemini, Docx, FileManager) в данный момент недоступны.")
        return

    photo_paths = []
    
    try:
        # 1. Скачивание файлов
        try:
            photo_paths = await file_manager.download_photos(callback.bot, callback.from_user.id, file_ids)
        except Exception as e:
            logging.exception("Failed to download photos")
            await processing_msg.edit_text(f"❌ Не удалось скачать фото:\n{str(e)}\n\nПопробуйте отправить заново.")
            return

        # 2. Подготовка шаблона в отдельном потоке (I/O)
        template_path = Path("templates") / current_config["template"]
        output_path = file_manager.get_output_path(callback.from_user.id, file_ids[0])
        await asyncio.to_thread(docx_service.create_temp_template, template_path, current_config["name"], lang_name)
        
        # 3. Распознавание через Gemini
        total_photos = len(photo_paths)
        await processing_msg.edit_text(
            f"✅ Документ: **{current_config['name']}**\n✅ Язык перевода: **{lang_name}**\n\n📸 Фото получено\n\n⏳ Обрабатываем документ...\n[2/3] Извлечение данных",
            parse_mode="Markdown"
        )
        
        extracted_data = await gemini_service.extract_data_from_image(
            image_path=photo_paths,
            prompt=current_config["prompt"]
        )
        
        if "error" in extracted_data:
            raise ValueError(f"Ошибка Gemini: {extracted_data['error']}\n{extracted_data.get('raw_text', '')}")

        # 4. Обновление состояния и переход к валидации
        await processing_msg.edit_text(
            f"✅ Документ: **{current_config['name']}**\n✅ Язык перевода: **{lang_name}**\n\n📸 Фото получено\n\n✅ Обработка завершена\n[3/3] Подготовка документа",
            parse_mode="Markdown"
        )
        await asyncio.sleep(1)
        
        await state.update_data(
            extracted_data=extracted_data,
            template_path=str(template_path),
            output_path=str(output_path),
            lang_name=lang_name,
            lang_code=lang
        )
        await state.set_state(TranslationState.validating_data)
        
        await processing_msg.delete()
        await send_validation_menu(callback.message, extracted_data, lang_name, lang)
        
    except ValueError as e:
        logging.warning(f"Recognition failed during processing: {e}")
        retry_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📸 Отправить новое фото", callback_data="retry_photo")]
        ])
        await processing_msg.edit_text(ERROR_MSG_RECOGNITION, reply_markup=retry_kb)
        
    except Exception as e:
        logging.exception("Error processing document language pipeline")
        await processing_msg.edit_text(f"❌ Произошла ошибка при обработке:\n{str(e)}")
    finally:
        # Гарантированное удаление фото
        if file_manager:
            file_manager.cleanup_files(photo_paths)

def get_validation_keyboard(data_dict: dict, lang_code: str = "ru") -> InlineKeyboardMarkup:
    buttons = []
    current_row = []
    
    for key in data_dict.keys():
        localized_name = doc_manager.localize_field(key, lang_code)
        btn_text = f"✏️ {localized_name[:20]}"
        cb_data = f"editf_{key}"
        if len(cb_data) > 64:
            cb_data = cb_data[:64]
            
        current_row.append(InlineKeyboardButton(text=btn_text, callback_data=cb_data))
        
        if len(current_row) == 2:
            buttons.append(current_row)
            current_row = []
            
    if current_row:
        buttons.append(current_row)
    
    confirm_text = "✅ Подтвердить и создать" if lang_code == "ru" else "✅ Confirm and generate"
    buttons.append([InlineKeyboardButton(text=confirm_text, callback_data="confirm_generation")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def send_validation_menu(message: types.Message, data_dict: dict, lang_name: str = "выбранный", lang_code: str = "ru"):
    title = f"🤖 **Результат распознавания ({lang_name}):**\n" if lang_code == "ru" else f"🤖 **Extraction Result ({lang_name}):**\n"
    lines = [title]
    for k, v in data_dict.items():
        localized_name = doc_manager.localize_field(k, lang_code)
        lines.append(f"▪️ **{localized_name}**: `{v}`")
        
    instr = "\n_Нажмите на кнопку с именем поля ниже, если нужно его исправить._" if lang_code == "ru" else "\n_Click on the field name below if you need to manually fix it._"
    text = "\n".join(lines) + "\n" + instr
    
    await message.answer(text, reply_markup=get_validation_keyboard(data_dict, lang_code), parse_mode="Markdown")

@router.callback_query(F.data.startswith("editf_"), TranslationState.validating_data)
async def process_edit_field_selection(callback: CallbackQuery, state: FSMContext):
    field_key = callback.data.replace("editf_", "")
    await state.update_data(editing_field_name=field_key)
    await state.set_state(TranslationState.editing_field)
    
    await callback.answer()
    
    data = await state.get_data()
    extracted_data = data.get("extracted_data", {})
    current_value = extracted_data.get(field_key, "")
    lang_code = data.get("lang_code", "ru")
    localized_name = doc_manager.localize_field(field_key, lang_code)
    
    prompt = (
        f"✏️ Введите новое значение для поля **{localized_name}**\nТекущее значение: `{current_value}`\n\n(Или отправьте /cancel для отмены редактирования)" 
        if lang_code == "ru" 
        else f"✏️ Enter new value for **{localized_name}**\nCurrent value: `{current_value}`\n\n(Or send /cancel to abort)"
    )
    
    await callback.message.answer(prompt, parse_mode="Markdown")

@router.message(TranslationState.editing_field)
async def process_new_field_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    extracted_data = data.get("extracted_data", {})
    lang_code = data.get("lang_code", "ru")
    lang_name = data.get("lang_name", "выбранный")

    if message.text == "/cancel":
        await state.set_state(TranslationState.validating_data)
        await send_validation_menu(message, extracted_data, lang_name, lang_code)
        return

    new_value = message.text
    field_key = data.get("editing_field_name")
    
    if field_key:
        extracted_data[field_key] = new_value
        await state.update_data(extracted_data=extracted_data)
    
    await state.set_state(TranslationState.validating_data)
    ok_msg = "✅ Значение изменено!" if lang_code == "ru" else "✅ Value updated!"
    await message.reply(ok_msg)
    await send_validation_menu(message, extracted_data, lang_name, lang_code)

@router.callback_query(F.data == "confirm_generation", TranslationState.validating_data)
async def confirm_generation(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    processing_msg = await callback.message.edit_text("⏳ Генерирую документ...")
    
    data = await state.get_data()
    extracted_data = data.get("extracted_data", {})
    
    template_path_str = data.get("template_path")
    output_path_str = data.get("output_path")
    
    if not template_path_str or not output_path_str:
        await processing_msg.edit_text("❌ Ошибка: пути к файлам не найдены в сессии. Начните заново.")
        await state.clear()
        return
        
    template_path = Path(template_path_str)
    output_path = Path(output_path_str)
    lang_name = data.get("lang_name", "Выбранный")
    
    gemini_service = get_gemini_service()
    docx_service = get_service("docx_service")
    file_manager = get_service("file_manager")
    
    if not gemini_service or not docx_service or not file_manager:
        await processing_msg.edit_text("❌ Сервисы (Gemini, Docx, FileManager) в данный момент недоступны.")
        return

    try:
        # Вставляем данные в Word (I/O, в отдельном потоке)
        await asyncio.to_thread(docx_service.generate_docx, extracted_data, template_path, output_path)
        
        # Отправляем готовый Word
        await processing_msg.edit_text("✅ Документ готов! Отправляю файл...")
        document = FSInputFile(output_path)
        await callback.message.answer_document(document, caption=f"Вот ваш проверенный перевод на {lang_name.lower()} язык!")
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Произошла ошибка при генерации документа:\n{str(e)}")
        
    finally:
        if file_manager:
            file_manager.cleanup_files([output_path])
        await state.clear()
