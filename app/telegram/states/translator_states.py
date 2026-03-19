from aiogram.fsm.state import StatesGroup, State

class TranslationState(StatesGroup):
    waiting_for_photos = State()
    choosing_doc_type = State()
    choosing_language = State()
    validating_data = State()
    editing_field = State()
    editing_raw_json = State()
    viewing_table = State()
    editing_table_row = State()
