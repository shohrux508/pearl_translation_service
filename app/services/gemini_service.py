import json
import logging
from pathlib import Path
from typing import Dict, Any, Union
import google.generativeai as genai
import PIL.Image

logger = logging.getLogger(__name__)

class GeminiTranslationService:
    """
    Сервис для работы с Gemini API:
    - Загрузка изображений
    - Извлечение данных в формате JSON
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """
        Инициализация сервиса Gemini.
        """
        if not api_key:
            raise ValueError("API ключ для Gemini не предоставлен.")
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        
        # Дефолтный промпт, чтобы не прокидывать его каждый раз
        self.default_prompt = (
            "Проанализируй предоставленные изображения (это могут быть лицевая и обратная стороны одного документа). "
            "Извлеки все значимые текстовые поля, используя информацию со всех переданных изображений, "
            "и верни их в виде плоского JSON словаря (ключ-значение, где оба строки). "
            "Ключи должны быть на английском (snake_case), соответствуя смыслу поля."
        )

    async def extract_data_from_image(
        self, 
        image_path: Union[str, Path, list[Union[str, Path]]] = None, 
        prompt: str = None,
        json_schema: Dict[str, Any] = None,
        test_json_response: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Отправляет одно или несколько изображений в Gemini и извлекает данные в JSON.
        """
        if test_json_response is not None:
            logger.info("Использован тестовый JSON ответ, вызов к API пропущен.")
            return test_json_response
            
        if not image_path:
            raise ValueError("Необходимо передать путь к изображению (image_path)")
            
        # Используем дефолтный промпт, если не передан свой
        current_prompt = prompt or self.default_prompt
        
        if json_schema:
            schema_instruction = (
                "\n\nReturn strictly valid JSON according to the provided schema. "
                "Do not include markdown formatting or explanations.\n"
                f"JSON Schema:\n{json.dumps(json_schema, ensure_ascii=False, indent=2)}"
            )
            current_prompt += schema_instruction
            
        try:
            contents = [current_prompt]
            
            if isinstance(image_path, list):
                logger.info(f"Отправка {len(image_path)} изображений в Gemini для анализа...")
                for p in image_path:
                    contents.append(PIL.Image.open(p))
            else:
                logger.info(f"Отправка изображения {image_path} в Gemini для анализа...")
                contents.append(PIL.Image.open(image_path))
            
            # Мы ожидаем, что Gemini вернет строго JSON
            response = await self.model.generate_content_async(
                contents,
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Парсим JSON ответ
            data = json.loads(response.text)
            logger.info("Успешно извлечены данные (JSON).")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при парсинге JSON от Gemini: {e}")
            logger.error(f"Сырой ответ: {response.text}")
            return {"error": "Invalid JSON response", "raw_text": response.text}
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при обращении к Gemini: {e}")
            raise e

    async def generate_field_translations(self, ru_fields: list[str]) -> list[dict]:
        """
        Берет список полей на русском и генерирует для них ключи и перевод на английский.
        Возвращает: [{"keyword": "...", "ru_name": "...", "en_name": "..."}, ...]
        """
        prompt = (
            "У меня есть список полей документа на русском языке. "
            "Для каждого поля сгенерируй:\n"
            "1. Уникальный 'keyword' (ключ) на английском в формате snake_case.\n"
            "2. 'en_name' (перевод на английский язык).\n"
            "Верни в формате JSON, где корнем является массив (строго list, не объект) объектов со строгими ключами: "
            "'keyword', 'ru_name', 'en_name'. Верни ТОЛЬКО JSON-массив и больше ничего.\n\n"
            f"Список полей: {ru_fields}"
        )
        
        try:
            logger.info(f"Отправка {len(ru_fields)} полей в Gemini для перевода и генерации ключей...")
            
            response = await self.model.generate_content_async(
                contents=prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            data = json.loads(response.text)
            
            # В случае если Gemini вернет объект {'fields': [...]}, обрабатываем:
            if isinstance(data, dict):
                # берем первую попавшуюся коллекцию если это dict
                for k, v in data.items():
                    if isinstance(v, list):
                        data = v
                        break
                
            logger.info("Успешно сгенерированы ключи и переводы (JSON).")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при парсинге JSON от Gemini (fields): {e}")
            raise ValueError("Invalid JSON response from Gemini")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при обращении к Gemini (fields): {e}")
            raise e

    async def analyze_document_for_template(self, image_path: Union[str, Path, list[Union[str, Path]]]) -> dict:
        """
        Анализирует изображение документа и автоматически генерирует для него структуру шаблона:
        1. doc_name - понятное название документа.
        2. fields - массив полей (keyword, ru_name, en_name).
        """
        prompt = (
            "You are a document analyzer. Review the provided document images. "
            "Determine the generic document name (e.g., 'Паспорт РФ', 'Свидетельство о рождении') and list all the fields that could be extracted from it. "
            "Provide the response strictly as a JSON object with this shape: "
            "{\n"
            '  "doc_name": "Generic document name in Russian",\n'
            '  "fields": [\n'
            '    {"keyword": "snake_case_english_key", "ru_name": "Field name in Russian", "en_name": "Field name in English"}\n'
            '  ]\n'
            "}"
        )
        
        try:
            logger.info("Отправка документа в Gemini для анализа шаблона...")
            contents = [prompt]
            
            if isinstance(image_path, list):
                for p in image_path:
                    contents.append(PIL.Image.open(p))
            else:
                contents.append(PIL.Image.open(image_path))
                
            response = await self.model.generate_content_async(
                contents,
                generation_config={"response_mime_type": "application/json"}
            )
            
            data = json.loads(response.text)
            logger.info("Успешно проанализирован шаблон документа (JSON).")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при парсинге JSON от Gemini (analyze_document): {e}")
            raise ValueError("Invalid JSON response from Gemini")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при обращении к Gemini (analyze_document): {e}")
            raise e



