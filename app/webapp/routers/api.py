from fastapi import APIRouter, Request, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel
from app.services.document_manager import doc_manager
from app.config import settings
from pathlib import Path
import asyncio

router = APIRouter(prefix="/api/templates", tags=["templates_api"])

async def process_and_send_document(container, file_path: Path, doc_id: str, lang: str, user_id: int):
    gemini_service = container.get("gemini_service")
    docx_service = container.get("docx_service")
    file_manager = container.get("file_manager")
    
    import logging
    logger = logging.getLogger(__name__)

    try:
        current_config = doc_manager.get_document_config(doc_id, lang)
        if not current_config:
            logger.error(f"Unknown document type {doc_id} or language {lang}")
            return

        lang_name = "Русский" if lang == "ru" else "Английский"
        
        # Extract data using Gemini
        extracted_data = await gemini_service.extract_data_from_image(
            image_path=[str(file_path)],
            prompt=current_config["prompt"],
            json_schema=current_config.get("json_schema"),
            use_pro=False
        )
        
        if "error" in extracted_data:
            raise ValueError(f"Gemini error: {extracted_data['error']}")

        # Map data for docx (flatten fields and tables)
        pass_data = {}
        pass_data.update(extracted_data.get("fields", {}))
        pass_data.update(extracted_data.get("tables", {}))
        for k, v in extracted_data.items():
            if k not in ["fields", "tables", "metadata"]:
                pass_data[k] = v

        # Generate Document
        template_path = Path("templates") / current_config["template"]
        output_path = file_manager.get_output_path(user_id, file_path.stem)
        
        await asyncio.to_thread(docx_service.create_temp_template, template_path, current_config["name"], lang_name)
        await asyncio.to_thread(docx_service.generate_docx, pass_data, template_path, output_path)

        # Send via Bot
        from aiogram import Bot
        from aiogram.types import FSInputFile
        
        bot = Bot(token=settings.BOT_TOKEN)
        try:
            document = FSInputFile(output_path)
            await bot.send_document(
                chat_id=user_id, 
                document=document, 
                caption=f"✅ Готово!\nВаш переведенный документ WebApp: {current_config['name']}"
            )
        finally:
            await bot.session.close()

    except Exception as e:
        logger.exception("Failed to process WebApp upload translation")
        from aiogram import Bot
        bot = Bot(token=settings.BOT_TOKEN)
        try:
            await bot.send_message(chat_id=user_id, text=f"❌ Произошла ошибка при выполнении WebApp перевода: {e}")
        finally:
            await bot.session.close()
    finally:
        # Cleanup temp upload file
        if file_manager:
            file_manager.cleanup_files([file_path])
        else:
            if file_path.exists():
                file_path.unlink()

@router.get("")
@router.get("/")
async def get_templates():
    types = doc_manager.get_types()
    templates_dir = Path("templates")
    
    result = []
    for t_id, info in types.items():
        ru_exists = (templates_dir / f"{t_id.upper()}_TEMPLATE_RU.docx").exists()
        en_exists = (templates_dir / f"{t_id.upper()}_TEMPLATE_EN.docx").exists()
        
        result.append({
            "id": t_id,
            "name": info.get("name", t_id),
            "emoji": info.get("emoji", "📄"),
            "ru_template": ru_exists,
            "en_template": en_exists
        })
        
    return result

@router.post("/upload")
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_id: str = Form(...),
    lang: str = Form("ru"),
    user_id: int = Form(...)
):
    container = request.app.state.container
    file_manager = container.get("file_manager")
    
    # Save the file temporarily
    import uuid
    import shutil
    
    file_ext = Path(file.filename).suffix
    temp_filename = f"webapp_{uuid.uuid4()}{file_ext}"
    temp_path = Path("temp") / temp_filename
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Queue background processing
    background_tasks.add_task(
        process_and_send_document,
        container=container,
        file_path=temp_path,
        doc_id=doc_id,
        lang=lang,
        user_id=user_id
    )
    
    return {"status": "ok", "message": "Translation queued"}
