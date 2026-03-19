from app.telegram.views.translator_texts import get_validation_text

def test_get_validation_text_flat():
    data = {"name": "John", "age": "30"}
    text = get_validation_text(data, lang_name="English", lang_code="en")
    assert "Extraction Result (English)" in text
    assert "John" in text
    assert "30" in text

def test_get_validation_text_schema():
    data = {
        "fields": {"first_name": "Ivan"},
        "tables": {"grades": [{"math": "5"}, {"physics": "4"}]}
    }
    text = get_validation_text(data, lang_name="Russian", lang_code="ru")
    assert "Результат распознавания (Russian)" in text
    assert "Ivan" in text
    assert "строк" in text or "rows" in text
