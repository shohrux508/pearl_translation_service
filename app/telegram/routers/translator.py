import os
import json
from pathlib import Path
from aiogram import Router, types, F
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from app.container import Container

router = Router()
container_instance: Container = None

class TranslationState(StatesGroup):
    choosing_doc_type = State()
    choosing_language = State()
    validating_data = State()
    editing_field = State()

from app.services.document_manager import doc_manager

def setup_router(container: Container):
    """
    Инжектим контейнер в роутер.
    """
    global container_instance
    container_instance = container

@router.message(F.photo)
async def handle_document_photo(message: types.Message, state: FSMContext):
    """
    Принимает фотографию документа от пользователя и предлагает выбрать тип.
    """
    # 1. Проверяем, что сервис зарегистрирован
    try:
        container_instance.get("gemini_service")
    except KeyError:
        await message.reply("❌ Сервис перевода (Gemini) в данный момент недоступен. Проверьте API ключ.")
        return

    # 2. Сохраняем file_id фото для дальнейшего скачивания
    photo = message.photo[-1]
    await state.update_data(file_id=photo.file_id)
    
    # 3. Формируем клавиатуру динамически
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
    
    await message.reply(
        "📸 Фото получено!\nПожалуйста, выберите тип документа, чтобы мы могли правильно его перевести:",
        reply_markup=keyboard
    )
    await state.set_state(TranslationState.choosing_doc_type)

@router.callback_query(F.data.startswith("doctype_"), TranslationState.choosing_doc_type)
async def process_document_type(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор типа документа и предлагает выбрать язык перевода.
    """
    doc_type = callback.data.replace("doctype_", "")
    
    # Сохраняем выбранный тип документа
    await state.update_data(doc_type=doc_type)
    
    # Формируем клавиатуру для выбора языка
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский язык", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 Английский язык", callback_data="lang_en")]
    ])
    
    # Подтверждаем клик
    await callback.answer()
    
    await callback.message.edit_text(
        "✅ Тип документа выбран.\n\n🌐 Теперь, пожалуйста, выберите язык, на который нужно перевести данные:",
        reply_markup=keyboard
    )
    await state.set_state(TranslationState.choosing_language)

@router.callback_query(F.data.startswith("lang_"), TranslationState.choosing_language)
async def process_language(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор языка и запускает пайплайн распознавания и перевода.
    """
    lang = callback.data.replace("lang_", "")
    
    data = await state.get_data()
    doc_type = data.get("doc_type")
    file_id = data.get("file_id")
    await state.clear()
    
    if not file_id or not doc_type:
        await callback.message.edit_text("❌ Ошибка: сессия устарела или данные не найдены. Пожалуйста, отправьте фото документа заново.")
        return

    # Настройки языка
    lang_name = "Русский" if lang == "ru" else "Английский"

    # Получаем конфигурацию (промпт, имя шаблона)
    current_config = doc_manager.get_document_config(doc_type, lang)
    if not current_config:
        await callback.answer("Неизвестный тип документа", show_alert=True)
        return

    # Подтверждаем клик
    await callback.answer()
    processing_msg = await callback.message.edit_text(
        f"✅ Документ: **{current_config['name']}**\n✅ Язык перевода: **{lang_name}**\n\n⏳ Подготавливаю фото и отправляю на анализ ИИ...", 
        parse_mode="Markdown"
    )

    # Получаем сервис
    try:
        gemini_service = container_instance.get("gemini_service")
    except KeyError:
        await processing_msg.edit_text("❌ Сервис перевода (Gemini) в данный момент недоступен. Проверьте API ключ.")
        return

    # Создаем директории
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    
    photo_path = temp_dir / f"doc_{callback.from_user.id}_{file_id}.jpg"
    
    # Скачиваем файл через bot.get_file
    try:
        file = await callback.bot.get_file(file_id)
        await callback.bot.download_file(file.file_path, destination=photo_path)
    except Exception as e:
        await processing_msg.edit_text(f"❌ Не удалось скачать фото:\n{str(e)}\n\nПопробуйте отправить заново.")
        return
    
    # Шаблоны и пути
    template_path = Path("templates") / current_config["template"]
    output_path = temp_dir / f"result_{callback.from_user.id}_{file_id}.docx"
    
    # Если шаблона еще нет, создаем пустышку для теста
    if not template_path.exists():
        template_path.parent.mkdir(exist_ok=True)
        from docx import Document
        doc = Document()
        doc.add_paragraph(f"Временный тестовый шаблон для: {current_config['name']}")
        doc.add_paragraph(f"Язык шаблона (и перевода): {lang_name}")
        doc.add_paragraph("Данные будут автоматически вставляться, если шаблонизатор найдет совпадающие поля (например {{surname}}).")
        doc.save(template_path)
        
    try:
        # Обновляем статус
        await processing_msg.edit_text(f"⏳ Изображение анализируется ИИ Gemini...\n\nТип: {current_config['name']}\nПеревод на: {lang_name}")
        
        # Вызываем сервис
        extracted_data = await gemini_service.extract_data_from_image(
            image_path=photo_path,
            prompt=current_config["prompt"]
        )
        
        if "error" in extracted_data:
            raise ValueError(f"Ошибка Gemini: {extracted_data['error']}\n{extracted_data.get('raw_text', '')}")

        # Удаляем фото, так как оно больше не нужно
        if photo_path.exists():
            os.remove(photo_path)

        await state.update_data(
            extracted_data=extracted_data,
            template_path=str(template_path),
            output_path=str(output_path),
            lang_name=lang_name,
            lang_code=lang
        )
        await state.set_state(TranslationState.validating_data)
        
        await processing_msg.delete()
        await send_validation_menu(processing_msg, extracted_data, lang_name, lang)
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Произошла ошибка при обработке:\n{str(e)}")
        if photo_path.exists():
            os.remove(photo_path)

def get_validation_keyboard(data_dict: dict, lang_code: str = "ru") -> InlineKeyboardMarkup:
    buttons = []
    current_row = []
    
    for key in data_dict.keys():
        localized_name = doc_manager.localize_field(key, lang_code)
        # Ограничиваем длину текста на кнопке
        btn_text = f"✏️ {localized_name[:20]}"
        
        # restriction is 64 bytes.
        cb_data = f"editf_{key}"
        if len(cb_data) > 64:
            cb_data = cb_data[:64]
            
        current_row.append(InlineKeyboardButton(text=btn_text, callback_data=cb_data))
        
        # По 2 кнопки в ряд
        if len(current_row) == 2:
            buttons.append(current_row)
            current_row = []
            
    # Добавляем оставшуюся кнопку, если есть
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
    if message.text == "/cancel":
        await state.set_state(TranslationState.validating_data)
        data = await state.get_data()
        await send_validation_menu(message, data.get("extracted_data", {}), data.get("lang_name", "выбранный"), data.get("lang_code", "ru"))
        return

    new_value = message.text
    data = await state.get_data()
    field_key = data.get("editing_field_name")
    extracted_data = data.get("extracted_data", {})
    lang_code = data.get("lang_code", "ru")
    
    # Обновляем значение
    extracted_data[field_key] = new_value
    await state.update_data(extracted_data=extracted_data)
    
    await state.set_state(TranslationState.validating_data)
    ok_msg = "✅ Значение изменено!" if lang_code == "ru" else "✅ Value updated!"
    await message.reply(ok_msg)
    await send_validation_menu(message, extracted_data, data.get("lang_name", "выбранный"), lang_code)

@router.callback_query(F.data == "confirm_generation", TranslationState.validating_data)
async def confirm_generation(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    processing_msg = await callback.message.edit_text("⏳ Генерирую документ...")
    
    data = await state.get_data()
    extracted_data = data.get("extracted_data", {})
    template_path = Path(data.get("template_path"))
    output_path = Path(data.get("output_path"))
    lang_name = data.get("lang_name", "Выбранный")
    
    try:
        gemini_service = container_instance.get("gemini_service")
        
        # Вставляем данные в Word
        gemini_service.insert_into_docx(
            data=extracted_data,
            template_path=template_path,
            output_path=output_path
        )
        
        # Отправляем готовый Word
        await processing_msg.edit_text("✅ Документ готов! Отправляю файл...")
        
        document = FSInputFile(output_path)
        await callback.message.answer_document(document, caption=f"Вот ваш проверенный перевод на {lang_name.lower()} язык!")
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Произошла ошибка при генерации документа:\n{str(e)}")
        
    finally:
        if output_path.exists():
            os.remove(output_path)
        await state.clear()
