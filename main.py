# main.py
from bot.telegram_bot import run_bot
from utils.config import TELEGRAM_BOT_TOKEN
from utils.logger import logger

if __name__ == "__main__":
    logger.info("Запуск основного приложения (Playwright, async).")
    run_bot(TELEGRAM_BOT_TOKEN)
