from app.services.document_manager import doc_manager

# 1. Определяем желаемую JSON-схему для Приложения к диплому
diploma_schema = {
    "type": "object",
    "properties": {
        "metadata": {
            "type": "object",
            "properties": {
                "doc_type": {"type": "string", "const": "diploma_supplement"},
                "language": {"type": "string", "enum": ["ru", "en"]}
            },
            "required": ["doc_type", "language"]
        },
        "fields": {
            "type": "object",
            "properties": {
                "fullname": {"type": "string", "description": "ФИО студента (например: Солижанов Шохбоз Фахрутдин Угли)"},
                "birth_date": {"type": "string", "description": "Дата рождения"},
                "specialization": {"type": "string", "description": "Специальность (например: 5321000 - Пищевая технология)"},
                "gpa": {"type": "string", "description": "Средний балл (GPA)"}
            },
            "required": ["fullname", "birth_date", "specialization"]
        },
        "tables": {
            "type": "object",
            "properties": {
                "academic_records": {
                    "type": "array",
                    "description": "Список всех изученных предметов с оценками и часами",
                    "items": {
                        "type": "object",
                        "properties": {
                            "n": {"type": "integer", "description": "Порядковый номер предмета"},
                            "subject": {"type": "string", "description": "Название предмета (например: Информационные технологии)"},
                            "hours": {"type": "integer", "description": "Количество академических часов"},
                            "grade": {"type": "string", "description": "Оценка (например: 5/5, отлично, зачтено)"}
                        },
                        "required": ["subject", "hours", "grade"]
                    }
                },
                "practices": {
                    "type": "array",
                    "description": "Список практик",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Название практики"},
                            "hours": {"type": "integer"}
                        }
                    }
                }
            },
            "required": ["academic_records"]
        }
    },
    "required": ["metadata", "fields", "tables"]
}

# 2. Переводы интерфейса (чтобы в боте отображалось красиво)
ru_translations = {
    "fullname": "ФИО",
    "birth_date": "Дата рождения",
    "specialization": "Специальность",
    "gpa": "Средний балл",
    "academic_records": "Предметы и оценки",
    "practices": "Практики"
}

en_translations = {
    "fullname": "Full Name",
    "birth_date": "Date of Birth",
    "specialization": "Specialization",
    "gpa": "GPA",
    "academic_records": "Academic Records",
    "practices": "Practices"
}

# 3. Добавляем новый тип документа в систему
doc_manager.add_document_type(
    doc_id="diploma_v2",
    name="Приложение к диплому (Схема)",
    emoji="🎓",
    prompt_fields="""
Извлеки данные из диплома в строгом соответствии с JSON-схемой.
Таблица с предметами (academic_records) должна содержать все предметы из документа.
    """,
    ru_translations=ru_translations,
    en_translations=en_translations,
    json_schema=diploma_schema
)

print("Document 'Schema Diploma' successfully added to documents.json!")
