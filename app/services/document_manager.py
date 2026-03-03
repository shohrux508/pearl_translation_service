import json
from pathlib import Path

class DocumentManager:
    def __init__(self, data_path: str | Path = "documents.json"):
        self.data_path = Path(data_path)
        self.reload()

    def reload(self):
        if not self.data_path.exists():
            self.data = {"document_types": {}, "configs": {}, "field_names": {"ru": {}, "en": {}}}
        else:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)

    def save(self):
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def get_types(self) -> dict:
        return self.data.get("document_types", {})

    def localize_field(self, key: str, lang_code: str) -> str:
        return self.data.get("field_names", {}).get(lang_code, {}).get(key, key.replace("_", " ").title())

    def get_document_config(self, doc_type: str, lang: str) -> dict | None:
        doc_info = self.data.get("document_types", {}).get(doc_type)
        config_data = self.data.get("configs", {}).get(doc_type)
        if not doc_info or not config_data:
            return None

        lang_instruction = (
            "ОБЯЗАТЕЛЬНО переведи все извлеченные текстовые данные НА РУССКИЙ ЯЗЫК." if lang == "ru" 
            else "ОБЯЗАТЕЛЬНО переведи все извлеченные текстовые данные НА АНГЛИЙСКИЙ ЯЗЫК."
        )

        template_name = f"{doc_type.upper()}_TEMPLATE_{lang.upper()}.docx"
        prompt_fields = config_data.get("prompt_fields", "")
        
        prompt = (
            f"Проанализируй этот документ ({doc_info['name']}). {lang_instruction} "
            f"Извлеки все значимые поля в плоский JSON, строго используя ключи:\n{prompt_fields}"
        )

        return {
            "name": doc_info["name"],
            "template": template_name,
            "prompt": prompt
        }

    def add_document_type(self, doc_id: str, name: str, emoji: str, prompt_fields: str, ru_translations: dict, en_translations: dict):
        self.data.setdefault("document_types", {})[doc_id] = {"name": name, "emoji": emoji}
        self.data.setdefault("configs", {})[doc_id] = {"prompt_fields": prompt_fields}
        
        self.data.setdefault("field_names", {}).setdefault("ru", {}).update(ru_translations)
        self.data.setdefault("field_names", {}).setdefault("en", {}).update(en_translations)
        
        self.save()

    def delete_document_type(self, doc_id: str):
        if doc_id in self.data.get("document_types", {}):
            del self.data["document_types"][doc_id]
        if doc_id in self.data.get("configs", {}):
            del self.data["configs"][doc_id]
        self.save()
        
        # Удаляем шаблоны
        import os
        templates_dir = Path("templates")
        ru_template = templates_dir / f"{doc_id.upper()}_TEMPLATE_RU.docx"
        en_template = templates_dir / f"{doc_id.upper()}_TEMPLATE_EN.docx"
        
        if ru_template.exists():
            os.remove(ru_template)
        if en_template.exists():
            os.remove(en_template)

    def update_document_info(self, doc_id: str, name: str = None, emoji: str = None):
        doc = self.data.get("document_types", {}).get(doc_id)
        if doc:
            if name is not None:
                doc["name"] = name
            if emoji is not None:
                doc["emoji"] = emoji
            self.save()

# Global singleton
doc_manager = DocumentManager()
