import json

def get_mapping(key, old_data):
    ru_map = old_data.get("field_names", {}).get("ru", {})
    en_map = old_data.get("field_names", {}).get("en", {})
    return {
        "ru": ru_map.get(key, key),
        "en": en_map.get(key, key)
    }

def main():
    with open("documents.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    new_data = {
        "document_types": data.get("document_types", {}),
        "configs": {}
    }

    # ID Card
    id_card_fields = "given_name, surname, patronymic, citizenship, date_of_birth, card_number, date_of_issue, date_of_expiry, personal_identification_number, place_of_issue"
    id_card_config = {"fields": {}}
    for k in id_card_fields.split(", "):
        id_card_config["fields"][k] = {
            "type": "string",
            "ui_mapping": get_mapping(k, data)
        }
    new_data["configs"]["id_card"] = id_card_config

    # Passport
    passport_fields = "type, state_code, passport_number, surname, given_name, citizenship, date_of_birth, birth_place, date_of_issue, authority, date_of_expiry"
    passport_config = {"fields": {}}
    for k in passport_fields.split(", "):
        passport_config["fields"][k] = {
            "type": "string",
            "ui_mapping": get_mapping(k, data)
        }
    new_data["configs"]["passport"] = passport_config

    # Diploma v2
    diploma_config = {
        "fields": {
            "fullname": {
                "type": "string",
                "description": "ФИО студента (например: Солижанов Шохбоз Фахрутдин Угли)",
                "ui_mapping": get_mapping("fullname", data)
            },
            "birth_date": {
                "type": "string",
                "description": "Дата рождения",
                "ui_mapping": get_mapping("birth_date", data)
            },
            "specialization": {
                "type": "string",
                "description": "Специальность",
                "ui_mapping": get_mapping("specialization", data)
            },
            "gpa": {
                "type": "string",
                "description": "Средний балл (GPA)",
                "ui_mapping": get_mapping("gpa", data),
                "validation_logic": {
                    "max": 5.0
                }
            }
        },
        "tables": {
            "academic_records": {
                "description": "Список всех изученных предметов с оценками и часами",
                "ui_mapping": get_mapping("academic_records", data),
                "items": {
                    "n": {
                        "type": "integer",
                        "description": "Порядковый номер"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Название предмета",
                        "ui_mapping": get_mapping("subject", data)
                    },
                    "hours": {
                        "type": "integer",
                        "description": "Количество часов",
                        "ui_mapping": get_mapping("hours", data)
                    },
                    "grade": {
                        "type": "string",
                        "description": "Оценка",
                        "ui_mapping": get_mapping("grade", data)
                    }
                }
            },
            "practices": {
                "description": "Список практик",
                "ui_mapping": get_mapping("practices", data),
                "items": {
                    "title": {
                        "type": "string",
                        "description": "Название практики",
                        "ui_mapping": get_mapping("title", data)
                    },
                    "hours": {
                        "type": "integer",
                        "description": "Количество часов",
                        "ui_mapping": get_mapping("hours", data)
                    }
                }
            }
        }
    }
    
    # Let's fix missing strings in ui_mapping for missing fields
    def set_default(d, key, ru, en):
        if d.get("ui_mapping", {}).get("ru") == key:
            d["ui_mapping"]["ru"] = ru
        if d.get("ui_mapping", {}).get("en") == key:
            d["ui_mapping"]["en"] = en
            
    set_default(diploma_config["tables"]["academic_records"]["items"]["n"], "n", "№", "N")
    set_default(diploma_config["tables"]["academic_records"]["items"]["subject"], "subject", "Предмет", "Subject")
    set_default(diploma_config["tables"]["academic_records"]["items"]["hours"], "hours", "Часы", "Hours")
    set_default(diploma_config["tables"]["academic_records"]["items"]["grade"], "grade", "Оценка", "Grade")
    set_default(diploma_config["tables"]["practices"]["items"]["title"], "title", "Название", "Title")
    set_default(diploma_config["tables"]["practices"]["items"]["hours"], "hours", "Часы", "Hours")


    new_data["configs"]["diploma_v2"] = diploma_config

    with open("documents.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
