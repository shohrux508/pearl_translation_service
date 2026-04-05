"""
libs.utils.logger — Конфигурация логирования через Loguru.

Единая точка настройки для всего приложения.
Перехватывает стандартный logging (aiogram, uvicorn, etc.) → Loguru.
"""

import logging
import sys
from typing import Optional

from loguru import logger


class _InterceptHandler(logging.Handler):
    """
    Перехватчик стандартного logging → Loguru.
    
    Все библиотеки, использующие `logging.getLogger()` (aiogram, uvicorn, etc.),
    автоматически перенаправляются в Loguru с сохранением уровней.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Определяем уровень Loguru по имени уровня logging
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Ищем вызывающий фрейм вне logging
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_globals.get("__name__") == logging.__name__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logger(
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_mode: bool = False,
) -> None:
    """
    Настраивает Loguru как единый логгер приложения.

    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Путь к файлу логов. None = только консоль.
        json_mode: True = JSON-формат (для продакшена), False = человекочитаемый.
    """
    # Убираем дефолтный sink Loguru
    logger.remove()

    # ── Консольный вывод ─────────────────────────────────────────────
    if json_mode:
        logger.add(
            sys.stderr,
            level=level,
            serialize=True,  # JSON
        )
    else:
        logger.add(
            sys.stderr,
            level=level,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
                "<level>{message}</level>"
            ),
            colorize=True,
        )

    # ── Файловый вывод (опционально) ─────────────────────────────────
    if log_file:
        logger.add(
            log_file,
            level=level,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            serialize=json_mode,
            encoding="utf-8",
        )

    # ── Перехват стандартного logging ─────────────────────────────────
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)

    # Приглушаем шумные логгеры
    for noisy in ("httpx", "httpcore", "hpack"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logger.info("Логирование настроено (level={}, file={}, json={})", level, log_file or "—", json_mode)
