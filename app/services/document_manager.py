import json
from pathlib import Path

class DocumentManager:
    def __init__(self, data_path: str | Path = "documents.json"):
        self.data_path = Path(data_path)
        self.reload()

    def reload(self):
        if not self.data_path.exists():
            self.data = {"document_types": {}, "configs": {}}
        else:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)

    def save(self):
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def get_types(self) -> dict:
        return self.data.get("document_types", {})

    def localize_field(self, key: str, lang_code: str, doc_type: str = None) -> str:
        # If doc_type is given, search strictly there, otherwise search across all configs
        configs = self.data.get("configs", {})
        search_configs = [configs[doc_type]] if doc_type in configs else configs.values()
        
        for config in search_configs:
            # Check fields
            fields = config.get("fields", {})
            if key in fields:
                return fields[key].get("ui_mapping", {}).get(lang_code, key)
            
            # Check tables
            tables = config.get("tables", {})
            if key in tables:
                return tables[key].get("ui_mapping", {}).get(lang_code, key)
                
            for table_data in tables.values():
                items = table_data.get("items", {})
                if key in items:
                    return items[key].get("ui_mapping", {}).get(lang_code, key)
                    
        return key.replace("_", " ").title()

    def _generate_json_schema(self, config_data: dict, doc_type: str) -> dict:
        properties = {}
        required = []

        if "fields" in config_data:
            fields_props = {}
            for k, v in config_data["fields"].items():
                fields_props[k] = {
                    "type": v.get("type", "string")
                }
                if "description" in v:
                    fields_props[k]["description"] = v["description"]
            
            properties["fields"] = {
                "type": "object",
                "properties": fields_props,
                "required": list(fields_props.keys())
            }
            required.append("fields")

        if "tables" in config_data:
            tables_props = {}
            for tk, tv in config_data["tables"].items():
                items_props = {}
                for ik, iv in tv.get("items", {}).items():
                    items_props[ik] = {
                        "type": iv.get("type", "string")
                    }
                    if "description" in iv:
                        items_props[ik]["description"] = iv["description"]
                        
                tables_props[tk] = {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": items_props,
                        "required": list(items_props.keys())
                    }
                }
                if "description" in tv:
                    tables_props[tk]["description"] = tv["description"]
            
            properties["tables"] = {
                "type": "object",
                "properties": tables_props,
                "required": list(tables_props.keys())
            }
            required.append("tables")

        # Add metadata block automatically (useful for doc handling)
        properties["metadata"] = {
            "type": "object",
            "properties": {
                "doc_type": {"type": "string", "const": doc_type},
                "language": {"type": "string", "enum": ["ru", "en"]}
            },
            "required": ["doc_type", "language"]
        }
        required.append("metadata")
            
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }

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
        
        json_schema = self._generate_json_schema(config_data, doc_type)
        
        prompt = (
            f"Проанализируй этот документ ({doc_info['name']}). {lang_instruction} "
            "Извлеки данные строго в соответствии с предоставленной JSON-схемой."
        )

        return {
            "name": doc_info["name"],
            "template": template_name,
            "prompt": prompt,
            "json_schema": json_schema
        }

    def add_document_type(self, doc_id: str, name: str, emoji: str, config: dict):
        self.data.setdefault("document_types", {})[doc_id] = {"name": name, "emoji": emoji}
        self.data.setdefault("configs", {})[doc_id] = config
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
