import os
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

class FileManagerService:
    """
    Сервис для работы с временными файлами и скачиванием медиа.
    """
    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        
    async def download_photos(self, bot, user_id: int, file_ids: list) -> List[Path]:
        photo_paths = []
        for i, file_id in enumerate(file_ids):
            photo_path = self.temp_dir / f"doc_{user_id}_{file_id}_{i}.jpg"
            file = await bot.get_file(file_id)
            await bot.download_file(file.file_path, destination=photo_path)
            photo_paths.append(photo_path)
        return photo_paths
        
    def get_output_path(self, user_id: int, file_id: str, ext: str = ".docx") -> Path:
        return self.temp_dir / f"result_{user_id}_{file_id}{ext}"
        
    def cleanup_files(self, file_paths: List[Path]):
        for p in file_paths:
            if p and Path(p).exists():
                try:
                    os.remove(p)
                    logger.debug(f"Удален временный файл: {p}")
                except Exception as e:
                    logger.error(f"Не удалось удалить файл {p}: {e}")
