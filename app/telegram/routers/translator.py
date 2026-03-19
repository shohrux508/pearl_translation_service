import asyncio
import logging
from pathlib import Path
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from app.container import Container
from app.services.document_manager import doc_manager
from app.telegram.states.translator_states import TranslationState
from app.telegram.views.translator_texts import (
    START_GREETING, PHOTO_INSTRUCTION_TEXT, HELP_TEXT, ERROR_MSG_RECOGNITION, get_validation_text
)
from app.telegram.keyboards.translator_kb import (
    get_start_keyboard, get_flash_pro_keyboard, get_doc_types_keyboard,
    get_language_keyboard, get_retry_photo_keyboard, get_validation_keyboard,
    get_table_view_keyboard
)

router = Router()
container_instance: Container = None

def setup_router(container: Container):
    global container_instance
    container_instance = container

def get_service(name: str):
    try:
        return container_instance.get(name)
    except (KeyError, AttributeError):
        return None

def get_gemini_service():
    return get_service("gemini_service")

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(START_GREETING, reply_markup=get_start_keyboard(), parse_mode="Markdown")

@router.message(F.text == "📄 Перевод документа")
async def menu_translate(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(TranslationState.waiting_for_photos)
    await message.answer(PHOTO_INSTRUCTION_TEXT, reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")

@router.message(F.text == "❓ Как это работает?")
async def menu_help(message: types.Message):
    await message.answer(HELP_TEXT, parse_mode="Markdown")

@router.callback_query(F.data == "retry_photo")
async def retry_photo_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await state.set_state(TranslationState.waiting_for_photos)
    await callback.message.edit_text(PHOTO_INSTRUCTION_TEXT, parse_mode="Markdown")

@router.message(F.photo, TranslationState.waiting_for_photos)
async def handle_document_photo(message: types.Message, state: FSMContext):
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
    
    keyboard = get_flash_pro_keyboard()
    text = f"📄 Получено **{total_pages}** страниц документа\n\nМожете отправить еще фото, либо нажмите кнопку ниже для продолжения:"
    
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
             msg = await message.reply(text, reply_markup=keyboard, parse_mode="Markdown")
             await state.update_data(last_tracking_msg_id=msg.message_id)
    else:
        msg = await message.reply(text, reply_markup=keyboard, parse_mode="Markdown")
        await state.update_data(last_tracking_msg_id=msg.message_id)

@router.callback_query(F.data.startswith("start_recog_"), TranslationState.waiting_for_photos)
async def start_recognition_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    file_ids = data.get("file_ids", [])
    
    if not file_ids:
        await callback.message.answer("❌ Ошибка: фото не найдены. Отправьте фото заново.")
        return
        
    use_pro = callback.data.endswith("_pro")
    await state.update_data(use_pro=use_pro)
        
    await ask_for_doc_type(callback.message, state, edit_message=True)

async def ask_for_doc_type(message: types.Message, state: FSMContext, edit_message: bool = False) -> None:
    keyboard = get_doc_types_keyboard()
    text = "📸 Все фото получены!\nПожалуйста, выберите тип документа, чтобы мы могли правильно его перевести:"

    if edit_message:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await message.reply(text, reply_markup=keyboard)
        
    await state.set_state(TranslationState.choosing_doc_type)

@router.callback_query(F.data.startswith("doctype_"), TranslationState.choosing_doc_type)
async def process_document_type(callback: CallbackQuery, state: FSMContext):
    doc_type = callback.data.replace("doctype_", "")
    await state.update_data(doc_type=doc_type)
    
    keyboard = get_language_keyboard()
    
    await callback.answer()
    await callback.message.edit_text(
        "✅ Тип документа выбран.\n\n🌐 Теперь, пожалуйста, выберите язык, на который нужно перевести данные:",
        reply_markup=keyboard
    )
    await state.set_state(TranslationState.choosing_language)

@router.callback_query(F.data.startswith("lang_"), TranslationState.choosing_language)
async def process_language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.replace("lang_", "")
    data = await state.get_data()
    doc_type = data.get("doc_type")
    file_ids = data.get("file_ids", [])
    use_pro = data.get("use_pro", False)
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
        try:
            photo_paths = await file_manager.download_photos(callback.bot, callback.from_user.id, file_ids)
        except Exception as e:
            logging.exception("Failed to download photos")
            await processing_msg.edit_text(f"❌ Не удалось скачать фото:\n{str(e)}\n\nПопробуйте отправить заново.")
            return

        template_path = Path("templates") / current_config["template"]
        output_path = file_manager.get_output_path(callback.from_user.id, file_ids[0])
        await asyncio.to_thread(docx_service.create_temp_template, template_path, current_config["name"], lang_name)
        
        total_photos = len(photo_paths)
        model_tag = "Pro" if use_pro else "Flash"
        await processing_msg.edit_text(
            f"✅ Документ: **{current_config['name']}**\n✅ Язык перевода: **{lang_name}**\n\n📸 Фото получено\n\n⏳ Обрабатываем документ ({model_tag})...\n[2/3] Извлечение данных",
            parse_mode="Markdown"
        )
        
        extracted_data = await gemini_service.extract_data_from_image(
            image_path=photo_paths,
            prompt=current_config["prompt"],
            json_schema=current_config.get("json_schema"),
            use_pro=use_pro
        )
        
        if "error" in extracted_data:
            raise ValueError(f"Ошибка Gemini: {extracted_data['error']}\n{extracted_data.get('raw_text', '')}")

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
        retry_kb = get_retry_photo_keyboard()
        await processing_msg.edit_text(ERROR_MSG_RECOGNITION, reply_markup=retry_kb)
        
    except Exception as e:
        logging.exception("Error processing document language pipeline")
        await processing_msg.edit_text(f"❌ Произошла ошибка при обработке:\n{str(e)}")
    finally:
        if file_manager:
            file_manager.cleanup_files(photo_paths)

async def send_validation_menu(message: types.Message, data_dict: dict, lang_name: str = "выбранный", lang_code: str = "ru"):
    text = get_validation_text(data_dict, lang_name, lang_code)
    keyboard = get_validation_keyboard(data_dict, lang_code)
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "raw_json_mode", TranslationState.validating_data)
async def process_raw_json_mode(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    extracted_data = data.get("extracted_data", {})
    lang_code = data.get("lang_code", "ru")
    
    import json
    json_text = json.dumps(extracted_data, ensure_ascii=False, indent=2)
    
    prompt = (
        "⚙️ **Режим сырых данных (JSON)**\n\n"
        "Скопируйте текст ниже, исправьте нужные значения и отправьте обратно.\n"
        "Для отмены отправьте /cancel\n\n"
        f"```json\n{json_text}\n```"
    ) if lang_code == "ru" else (
        "⚙️ **Raw JSON Mode**\n\n"
        "Copy the текст below, fix the values and send it back.\n"
        "To cancel, send /cancel\n\n"
        f"```json\n{json_text}\n```"
    )
    
    await state.set_state(TranslationState.editing_raw_json)
    await callback.message.answer(prompt, parse_mode="Markdown")

@router.message(TranslationState.editing_raw_json)
async def process_new_raw_json(message: types.Message, state: FSMContext):
    data = await state.get_data()
    extracted_data = data.get("extracted_data", {})
    lang_code = data.get("lang_code", "ru")
    lang_name = data.get("lang_name", "выбранный")

    if message.text == "/cancel":
        await state.set_state(TranslationState.validating_data)
        await send_validation_menu(message, extracted_data, lang_name, lang_code)
        return

    import json
    try:
        new_data = json.loads(message.text)
        await state.update_data(extracted_data=new_data)
        await state.set_state(TranslationState.validating_data)
        
        ok_msg = "✅ Данные успешно обновлены!" if lang_code == "ru" else "✅ Data successfully updated!"
        await message.reply(ok_msg)
        await send_validation_menu(message, new_data, lang_name, lang_code)
    except json.JSONDecodeError:
        err_msg = "❌ Ошибка формата JSON. Пожалуйста, проверьте синтаксис и отправьте заново." if lang_code == "ru" else "❌ JSON format error. Please check syntax and send again."
        await message.reply(err_msg)

@router.callback_query(F.data.startswith("editf_"), TranslationState.validating_data)
async def process_edit_field_selection(callback: CallbackQuery, state: FSMContext):
    field_key = callback.data.replace("editf_", "")
    await state.update_data(editing_field_name=field_key)
    await state.set_state(TranslationState.editing_field)
    
    await callback.answer()
    
    data = await state.get_data()
    extracted_data = data.get("extracted_data", {})
    
    if "fields" in extracted_data:
        current_value = extracted_data.get("fields", {}).get(field_key, "")
    else:
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
        if "fields" in extracted_data:
            extracted_data["fields"][field_key] = new_value
        else:
            extracted_data[field_key] = new_value
            
        await state.update_data(extracted_data=extracted_data)
    
    await state.set_state(TranslationState.validating_data)
    ok_msg = "✅ Значение изменено!" if lang_code == "ru" else "✅ Value updated!"
    await message.reply(ok_msg)
    await send_validation_menu(message, extracted_data, lang_name, lang_code)

@router.callback_query(F.data.startswith("viewt_"), TranslationState.validating_data)
async def process_view_table(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.replace("viewt_", "").rsplit("_", 1)
    table_key = parts[0]
    page = int(parts[1]) if len(parts) > 1 else 0
    
    data = await state.get_data()
    extracted_data = data.get("extracted_data", {})
    lang_code = data.get("lang_code", "ru")
    
    tables = extracted_data.get("tables", {})
    table_data = tables.get(table_key, [])
    
    if not isinstance(table_data, list):
        await callback.answer("Ошибка: неверный формат таблицы", show_alert=True)
        return
        
    ITEMS_PER_PAGE = 5
    total_pages = (len(table_data) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    start_idx = page * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, len(table_data))
    
    await state.update_data(viewing_table_key=table_key, viewing_table_page=page)
    await state.set_state(TranslationState.viewing_table)
    
    localized_name = doc_manager.localize_field(table_key, lang_code)
    title = f"📊 **Таблица {localized_name}**" if lang_code == "ru" else f"📊 **Table {localized_name}**"
    
    lines = [f"{title} (стр. {page + 1} из {max(1, total_pages)})", ""]
    
    for i in range(start_idx, end_idx):
        row = table_data[i]
        preview = ", ".join([f"{k}: {v}" for k, v in list(row.items())[:2]])
        if len(preview) > 30: preview = preview[:27] + "..."
        lines.append(f"#{i+1}: `{preview}`")
        
    text = "\n".join(lines)
    keyboard = get_table_view_keyboard(table_key, page, total_pages, start_idx, end_idx, lang_code)
    
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "back_to_validation", TranslationState.viewing_table)
async def back_to_validation(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    extracted_data = data.get("extracted_data", {})
    lang_name = data.get("lang_name", "выбранный")
    lang_code = data.get("lang_code", "ru")
    
    await state.set_state(TranslationState.validating_data)
    await callback.message.delete()
    await send_validation_menu(callback.message, extracted_data, lang_name, lang_code)

@router.callback_query(F.data.startswith("editt_"), TranslationState.viewing_table)
async def process_edit_table_row(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.replace("editt_", "").rsplit("_", 1)
    table_key = parts[0]
    row_idx = int(parts[1])
    
    await state.update_data(editing_table_key=table_key, editing_row_idx=row_idx)
    await state.set_state(TranslationState.editing_table_row)
    
    await callback.answer()
    
    data = await state.get_data()
    extracted_data = data.get("extracted_data", {})
    tables = extracted_data.get("tables", {})
    row_data = tables.get(table_key, [])[row_idx]
    
    lang_code = data.get("lang_code", "ru")
    localized_name = doc_manager.localize_field(table_key, lang_code)
    
    import json
    json_text = json.dumps(row_data, ensure_ascii=False, indent=2)
    
    prompt = (
        f"✏️ **Редактирование строки {row_idx + 1} в ({localized_name})**\n\n"
        "Скопируйте JSON ниже, исправьте значения и отправьте обратно.\n"
        "Для отмены отправьте /cancel\n\n"
        f"```json\n{json_text}\n```"
    ) if lang_code == "ru" else (
        f"✏️ **Editing row {row_idx + 1} in ({localized_name})**\n\n"
        "Copy JSON below, fix values and send back.\n"
        "Send /cancel to abort\n\n"
        f"```json\n{json_text}\n```"
    )
    
    await callback.message.answer(prompt, parse_mode="Markdown")

@router.message(TranslationState.editing_table_row)
async def process_new_table_row_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    extracted_data = data.get("extracted_data", {})
    lang_code = data.get("lang_code", "ru")

    table_key = data.get("editing_table_key")
    row_idx = data.get("editing_row_idx")
    page = data.get("viewing_table_page", 0)

    if message.text == "/cancel":
        await state.set_state(TranslationState.viewing_table)
        ok_msg = "Действие отменено." if lang_code == "ru" else "Action cancelled."
        await message.reply(ok_msg)
        return

    import json
    try:
        new_row_data = json.loads(message.text)
        
        extracted_data["tables"][table_key][row_idx] = new_row_data
        await state.update_data(extracted_data=extracted_data)
        await state.set_state(TranslationState.viewing_table)
        
        ok_msg = "✅ Строка успешно обновлена!" if lang_code == "ru" else "✅ Row successfully updated!"
        await message.reply(ok_msg)
    except json.JSONDecodeError:
        err_msg = "❌ Ошибка формата JSON. Пожалуйста, проверьте синтаксис и отправьте заново." if lang_code == "ru" else "❌ JSON format error. Please check syntax and send again."
        await message.reply(err_msg)

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
        pass_data = {}
        pass_data.update(extracted_data.get("fields", {}))
        pass_data.update(extracted_data.get("tables", {}))
        for k, v in extracted_data.items():
            if k not in ["fields", "tables", "metadata"]:
                pass_data[k] = v
        
        await asyncio.to_thread(docx_service.generate_docx, pass_data, template_path, output_path)
        
        await processing_msg.edit_text("✅ Документ готов! Отправляю файл...")
        document = FSInputFile(output_path)
        await callback.message.answer_document(document, caption=f"Вот ваш проверенный перевод на {lang_name.lower()} язык!")
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Произошла ошибка при генерации документа:\n{str(e)}")
        
    finally:
        if file_manager:
            file_manager.cleanup_files([output_path])
        await state.clear()
