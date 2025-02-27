# utils/logger.py
from loguru import logger
import sys

# Устанавливаем формат логирования
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
           "<level>{message}</level>",
    level="DEBUG"
)

# Дополнительно можно указать лог-файл:
# logger.add("app.log", rotation="10 MB", level="DEBUG")
