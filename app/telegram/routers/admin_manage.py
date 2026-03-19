from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from app.container import Container
from app.services.document_manager import doc_manager
from pathlib import Path

router = Router()

class ManageDocState(StatesGroup):
    editing_name = State()
    editing_emoji = State()
    waiting_for_replace_ru = State()
    waiting_for_replace_en = State()

def setup_router(container: Container):
    pass

@router.message(F.text == "🗂 Мои шаблоны")
async def cmd_manage_docs(message: types.Message, state: FSMContext):
    """
    Открывает панель управления шаблонами.
    """
    await state.clear()
    await send_docs_list(message)

async def send_docs_list(message: types.Message | types.CallbackQuery, edit_message: bool = False):
    doc_types = doc_manager.get_types()
    buttons = []
    
    for doc_id, doc_info in doc_types.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{doc_info['emoji']} {doc_info['name']}",
                callback_data=f"mgmt_doc_{doc_id}"
            )
        ])
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    text = "📂 **Мои шаблоны**\nВыберите шаблон для просмотра, редактирования или удаления:"
    
    if edit_message:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        if isinstance(message, types.CallbackQuery):
            await message.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.reply(text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "mgmt_back_to_list")
async def back_to_list(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await send_docs_list(callback.message, edit_message=True)

@router.callback_query(F.data.startswith("mgmt_doc_"))
async def show_doc_details(callback: CallbackQuery, state: FSMContext):
    doc_id = callback.data.replace("mgmt_doc_", "")
    doc_types = doc_manager.get_types()
    if doc_id not in doc_types:
        await callback.answer("❌ Шаблон не найден!", show_alert=True)
        return
        
    doc_info = doc_types[doc_id]
    config_data = doc_manager.data.get("configs", {}).get(doc_id, {})
    
    # Store doc_id in state
    await state.update_data(current_mgmt_doc=doc_id)
    
    # Отправляем шаблоны если они есть
    templates_dir = Path("templates")
    ru_template = templates_dir / f"{doc_id.upper()}_TEMPLATE_RU.docx"
    en_template = templates_dir / f"{doc_id.upper()}_TEMPLATE_EN.docx"
    
    if ru_template.exists():
        await callback.message.answer_document(FSInputFile(ru_template), caption="📄 РУССКИЙ шаблон")
    if en_template.exists():
        await callback.message.answer_document(FSInputFile(en_template), caption="📄 АНГЛИЙСКИЙ шаблон")
    
    # Формируем список ключей
    fields_data = config_data.get("fields", {})
    keys_text = "🔑 **Доступные ключи для Word:**\n"
    if fields_data:
        for k, v in fields_data.items():
            ru_name = v.get("ui_mapping", {}).get("ru", k)
            keys_text += f"• `{{{{{k}}}}}` — {ru_name}\n"
    else:
        keys_text += "Нет полей\n"
    
    text = (
        f"📄 **Шаблон:** {doc_info['name']}\n"
        f"🆔 **Внутренний ID:** `{doc_id}`\n"
        f"😊 **Эмодзи:** {doc_info['emoji']}\n\n"
        f"{keys_text}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Заменить шаблон (RU)", callback_data=f"mgmt_replace_ru_{doc_id}")],
        [InlineKeyboardButton(text="🔄 Заменить шаблон (EN)", callback_data=f"mgmt_replace_en_{doc_id}")],
        [InlineKeyboardButton(text="✏️ Изменить название", callback_data=f"mgmt_edit_name_{doc_id}")],
        [InlineKeyboardButton(text="❌ Удалить шаблон", callback_data=f"mgmt_delete_{doc_id}")],
        [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="mgmt_back_to_list")]
    ])
    
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data.startswith("mgmt_delete_"))
async def delete_doc_confirm(callback: CallbackQuery):
    doc_id = callback.data.replace("mgmt_delete_", "")
    doc_manager.delete_document_type(doc_id)
    
    await callback.answer("✅ Шаблон успешно удален!", show_alert=True)
    await send_docs_list(callback.message, edit_message=True)

@router.callback_query(F.data.startswith("mgmt_edit_name_"))
async def edit_doc_name(callback: CallbackQuery, state: FSMContext):
    doc_id = callback.data.replace("mgmt_edit_name_", "")
    await state.update_data(current_mgmt_doc=doc_id)
    await state.set_state(ManageDocState.editing_name)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"mgmt_doc_{doc_id}")]
    ])
    
    await callback.message.edit_text("✏️ Отправьте новое название для этого шаблона:", reply_markup=keyboard)

@router.message(ManageDocState.editing_name)
async def save_doc_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    doc_id = data.get("current_mgmt_doc")
    new_name = message.text.strip()
    
    doc_manager.update_document_info(doc_id, name=new_name)
    await state.clear()
    
    await message.reply(f"✅ Название для `{doc_id}` успешно изменено на **{new_name}**.", parse_mode="Markdown")
    await send_docs_list(message)

@router.callback_query(F.data.startswith("mgmt_replace_ru_"))
async def start_replace_ru(callback: CallbackQuery, state: FSMContext):
    doc_id = callback.data.replace("mgmt_replace_ru_", "")
    await state.update_data(current_mgmt_doc=doc_id)
    await state.set_state(ManageDocState.waiting_for_replace_ru)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data=f"mgmt_doc_{doc_id}")]])
    await callback.message.edit_text("Отправьте новый файл `.docx` для **РУССКОГО** шаблона:", reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data.startswith("mgmt_replace_en_"))
async def start_replace_en(callback: CallbackQuery, state: FSMContext):
    doc_id = callback.data.replace("mgmt_replace_en_", "")
    await state.update_data(current_mgmt_doc=doc_id)
    await state.set_state(ManageDocState.waiting_for_replace_en)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data=f"mgmt_doc_{doc_id}")]])
    await callback.message.edit_text("Отправьте новый файл `.docx` для **АНГЛИЙСКОГО** шаблона:", reply_markup=keyboard, parse_mode="Markdown")

@router.message(ManageDocState.waiting_for_replace_ru, F.document)
async def process_replace_ru(message: types.Message, state: FSMContext):
    if not message.document.file_name.endswith('.docx'):
        await message.reply("❌ Пожалуйста, отправьте файл формата `.docx`.")
        return
        
    data = await state.get_data()
    doc_id = data.get("current_mgmt_doc")
    
    template_name = f"{doc_id.upper()}_TEMPLATE_RU.docx"
    save_path = Path("templates") / template_name
    save_path.parent.mkdir(exist_ok=True)
    
    await message.bot.download(message.document, destination=save_path)
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Вернуться к шаблону", callback_data=f"mgmt_doc_{doc_id}")]])
    await message.reply(f"✅ Русский шаблон для `{doc_id}` успешно обновлен!", reply_markup=keyboard, parse_mode="Markdown")

@router.message(ManageDocState.waiting_for_replace_en, F.document)
async def process_replace_en(message: types.Message, state: FSMContext):
    if not message.document.file_name.endswith('.docx'):
        await message.reply("❌ Пожалуйста, отправьте файл формата `.docx`.")
        return
        
    data = await state.get_data()
    doc_id = data.get("current_mgmt_doc")
    
    template_name = f"{doc_id.upper()}_TEMPLATE_EN.docx"
    save_path = Path("templates") / template_name
    save_path.parent.mkdir(exist_ok=True)
    
    await message.bot.download(message.document, destination=save_path)
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Вернуться к шаблону", callback_data=f"mgmt_doc_{doc_id}")]])
    await message.reply(f"✅ Английский шаблон для `{doc_id}` успешно обновлен!", reply_markup=keyboard, parse_mode="Markdown")
