import logging
from pathlib import Path
from typing import Dict, Any, Union
from docx import Document
from docxtpl import DocxTemplate

logger = logging.getLogger(__name__)

class DocxService:
    """
    Сервис для работы с Word-документами (.docx).
    Отвечает за генерацию и заполнение шаблонов.
    """
    
    def create_temp_template(self, template_path: Path, doc_name: str, lang_name: str) -> None:
        """
        Создает пустой тестовый шаблон, если его не существует.
        """
        if not template_path.exists():
            template_path.parent.mkdir(exist_ok=True, parents=True)
            doc = Document()
            doc.add_paragraph(f"Временный тестовый шаблон для: {doc_name}")
            doc.add_paragraph(f"Язык шаблона (и перевода): {lang_name}")
            doc.add_paragraph("Данные будут автоматически вставляться, если шаблонизатор найдет совпадающие поля (например {{surname}}).")
            doc.save(template_path)
            logger.info(f"Создан временный шаблон: {template_path}")

    def generate_docx(
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
