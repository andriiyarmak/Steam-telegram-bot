# steam/screenshot.py

import os
from utils.logger import logger
from playwright.async_api import Page

async def make_screenshot(page: Page, file_path: str) -> bool:
    try:
        logger.debug(f"Сохранение скриншота по пути: {file_path}")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        await page.screenshot(path=file_path)
        return True
    except Exception as e:
        logger.error(f"Ошибка при создании скриншота: {e}")
        return False
