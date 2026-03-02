import json
import logging
from pathlib import Path
from typing import Dict, Any, Union
from docxtpl import DocxTemplate
import google.generativeai as genai
import PIL.Image

logger = logging.getLogger(__name__)

class GeminiTranslationService:
    """
    Сервис для работы с Gemini API:
    - Загрузка изображений
    - Извлечение данных в формате JSON
    - Вставка извлеченных данных в Word (.docx) документ
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
            "Проанализируй этот документ. Извлеки все значимые текстовые поля "
            "и верни их в виде плоского JSON словаря (ключ-значение, где оба строки). "
            "Ключи должны быть на английском (snake_case), соответствуя смыслу поля."
        )

    async def extract_data_from_image(
        self, 
        image_path: Union[str, Path] = None, 
        prompt: str = None,
        test_json_response: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Отправляет изображение в Gemini и извлекает данные в JSON.
        Если передан test_json_response, возвращает его сразу (для мока/тестов).
        """
        if test_json_response is not None:
            logger.info("Использован тестовый JSON ответ, вызов к API пропущен.")
            return test_json_response
            
        if not image_path:
            raise ValueError("Необходимо передать путь к изображению (image_path)")
            
        # Используем дефолтный промпт, если не передан свой
        current_prompt = prompt or self.default_prompt
            
        try:
            # Загружаем изображение
            img = PIL.Image.open(image_path)
            
            logger.info(f"Отправка изображения {image_path} в Gemini для анализа...")
            
            # Мы ожидаем, что Gemini вернет строго JSON
            response = await self.model.generate_content_async(
                [current_prompt, img],
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

    def insert_into_docx(
        self, 
        data: Dict[str, Any], 
        template_path: Union[str, Path], 
        output_path: Union[str, Path]
    ) -> str:
        """
        Берет JSON-словарь извлеченных данных и заменяет плейсхолдеры 
        (например, {{key}}) в .docx шаблоне.
        """
        logger.info(f"Открытие шаблона {template_path} для вставки данных...")
        doc = DocxTemplate(template_path)
        doc.render(data)
        doc.save(output_path)
        logger.info(f"Документ успешно сохранен: {output_path}")
        return output_path

    async def process_translation(
        self, 
        template_path: Union[str, Path], 
        output_path: Union[str, Path],
        image_path: Union[str, Path] = None, 
        prompt: str = None, 
        test_json_response: Dict[str, Any] = None
    ) -> str:
        """
        Полный цикл сценария: Изображение -> Данные (JSON) -> .docx
        При тестировании можно передать test_json_response и пропустить шаг Gemini.
        """
        # Шаг 1: Извлекаем JSON (от API или из тестовых данных)
        extracted_data = await self.extract_data_from_image(
            image_path=image_path, 
            prompt=prompt, 
            test_json_response=test_json_response
        )
        
        if "error" in extracted_data:
            logger.error("Процесс был прерван из-за ошибки извлечения.")
            raise ValueError("Не удалось корректно извлечь данные.")

        # Шаг 2: Вставляем извлеченный JSON в шаблон Word
        result_path = self.insert_into_docx(extracted_data, template_path, output_path)
        
        return result_path
