# steam/login.py

import random
import asyncio
import os
from playwright.async_api import async_playwright, Page, TimeoutError
from utils.logger import logger

class SteamLogin:
    def __init__(self, headless: bool = True):
        """
        :param headless: Запускать ли браузер без интерфейса (True = headless).
        """
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page: Page | None = None

    async def start_browser(self):
        logger.info("Playwright: инициализация браузера SteamLogin (async)...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        # Если имеется сохранённое состояние сессии – используем его
        state_file = "storage_state.json"
        if os.path.exists(state_file):
            context = await self.browser.new_context(storage_state=state_file)
            logger.info("Состояние сессии загружено из %s", state_file)
        else:
            context = await self.browser.new_context()
            logger.info("Состояние сессии не найдено, создаём новый контекст.")
        self.page = await context.new_page()
        await self.page.set_viewport_size({"width": 1280, "height": 1024})
        logger.info(f"Playwright (async): браузер успешно инициализирован (headless={self.headless}).")

    async def open_steam_login_page(self):
        if not self.browser:
            await self.start_browser()
        url = "https://store.steampowered.com/login/?l=english"
        logger.info(f"Переходим на страницу логина Steam: {url}")
        await self.page.goto(url)

    async def is_logged_in(self) -> bool:
        """
        Проверяем, залогинен ли пользователь (ищем элемент #account_pulldown).
        """
        if not self.page:
            return False
        try:
            await self.page.wait_for_selector("#account_pulldown", timeout=3000)
            return True
        except TimeoutError:
            return False

    async def recover_session(self) -> bool:
        """
        Если текущий URL содержит "store.steampowered.com/login", пытаемся восстановить сессию
        из файла storage_state.json, создавая новый контекст и новую страницу.
        """
        state_file = "storage_state.json"
        if os.path.exists(state_file):
            logger.info("Обнаружена страница логина, восстанавливаем сессию из %s", state_file)
            context = await self.browser.new_context(storage_state=state_file)
            self.page = await context.new_page()
            try:
                await self.page.wait_for_selector("#account_pulldown", timeout=5000)
            except TimeoutError:
                logger.error("Не удалось восстановить сессию – элемент #account_pulldown не найден.")
                return False
            logger.info("Сессия успешно восстановлена.")
            return True
        else:
            logger.warning("Файл состояния сессии (%s) не найден.", state_file)
            return False

    async def ensure_session(self) -> bool:
        """
        Проверяет, не находится ли текущий URL на странице логина.
        Если да – пытается восстановить сессию.
        Возвращает True, если сессия валидна.
        """
        if not self.page:
            return False
        current_url = self.page.url
        if "store.steampowered.com/login" in current_url:
            return await self.recover_session()
        return True

    async def close_browser(self):
        if self.page:
            logger.info("Закрываем вкладку...")
            await self.page.close()
            self.page = None
        if self.browser:
            logger.info("Закрываем браузер...")
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
            logger.info("Playwright остановлен.")

    async def send_random_friend_message_advanced(self, message_text: str) -> bool:
        """
        1. Переходим на страницу друзей: https://steamcommunity.com/id/marshalzl/friends/
        2. Собираем все ссылки a.selectable_overlay (профили друзей).
        3. Выбираем случайного, переходим по ссылке.
        4. Ищем кнопку a.btn_profile_action.btn_medium с href^="javascript:OpenFriendChat(" и кликаем.
        5. Нажимаем кнопку div.btn_green_steamui.btn_medium (запустить веб-чат).
        6. Ждём 5 секунд и принудительно переходим на https://steamcommunity.com/chat/ в той же вкладке.
        7. На странице /chat/ ищем textarea и кнопку отправки, вводим сообщение и кликаем.
        Перед ключевыми действиями проверяем, что сессия не потерялась, вызывая ensure_session().
        """
        if not self.page:
            logger.error("send_random_friend_message_advanced: Page не инициализирована.")
            return False

        # Если случайно обнаружили страницу логина, восстанавливаем сессию
        if not await self.ensure_session():
            logger.error("Сессия не восстановлена, прерываем выполнение команды.")
            return False
        
        # 1) Открываем страницу друзей
        friends_url = "https://steamcommunity.com/id/marshalzl/friends/"
        logger.info(f"Переходим на страницу друзей: {friends_url}")
        await self.page.goto(friends_url)
        await asyncio.sleep(2)

        # 2) Собираем ссылки на друзей
        friend_links = await self.page.query_selector_all("a.selectable_overlay")
        if not friend_links:
            logger.warning("Не найдено ни одной ссылки на друга (a.selectable_overlay).")
            return False
        friend_urls = []
        for link in friend_links:
            href = await link.get_attribute("href")
            if href:
                friend_urls.append(href)
        if not friend_urls:
            logger.warning("Список ссылок друзей пуст. Возможно, нет друзей или неверный селектор.")
            return False

        # 3) Выбираем случайного друга
        random_url = random.choice(friend_urls)
        logger.info(f"Случайно выбран профиль друга: {random_url}")
        await self.page.goto(random_url)
        await asyncio.sleep(2)
        # Перед продолжением убеждаемся, что сессия восстановлена (не на странице логина)
        if not await self.ensure_session():
            logger.error("Сессия не восстановлена после перехода на /chat/.")
            return False

        # 4) Ищем кнопку для открытия чата
        try:
            chat_button = await self.page.wait_for_selector(
                'a.btn_profile_action.btn_medium[href^="javascript:OpenFriendChat("]',
                timeout=10000
            )
        except TimeoutError:
            logger.error("Кнопка для открытия чата (OpenFriendChat) не найдена. Проверьте селекторы.")
            return False
        logger.info("Нашли кнопку для открытия friend chat. Кликаем...")
        await chat_button.click()
        await asyncio.sleep(2)

        # 5) Нажимаем кнопку "Использовать веб-чат"
        try:
            webchat_button = await self.page.wait_for_selector(
                "div.btn_green_steamui.btn_medium",
                timeout=10000
            )
        except TimeoutError:
            logger.error("Кнопка 'btn_green_steamui.btn_medium' не появилась. Проверьте селекторы.")
            return False
        logger.info("Нажимаем кнопку 'Использовать веб-чат'...")
        await webchat_button.click()

        # Перед продолжением убеждаемся, что сессия восстановлена (не на странице логина)
        if not await self.ensure_session():
            logger.error("Сессия не восстановлена после перехода на /chat/.")
            return False
        
        # 6) Ждём 5 секунд, затем принудительно переходим на /chat/
        logger.info("Ждём 5 секунд и переходим на https://steamcommunity.com/chat/ ...")
        await asyncio.sleep(5)
        await self.page.goto("https://steamcommunity.com/chat/")
        await asyncio.sleep(3)

        # Перед продолжением убеждаемся, что сессия восстановлена (не на странице логина)
        if not await self.ensure_session():
            logger.error("Сессия не восстановлена после перехода на /chat/.")
            return False

        # 7) На странице /chat/ ищем textarea для ввода сообщения
        logger.info("На странице /chat/ ищем textarea для ввода сообщения...")
        try:
            message_textarea = await self.page.wait_for_selector(
                "textarea.chatentry_chatTextarea_113iu",
                timeout=10000
            )
        except TimeoutError:
            logger.error("Textarea для ввода сообщения на /chat/ не появилась. Проверьте селектор.")
            return False

        logger.info("Вводим сообщение и отправляем...")
        await message_textarea.fill(message_text)
        send_button = await self.page.query_selector("button.chatentry_chatSubmitButton_RVIs8")
        if not send_button:
            logger.error("Кнопка отправки сообщения не найдена на /chat/.")
            return False

        await asyncio.sleep(1)
        await send_button.click()
        logger.info("Сообщение успешно отправлено через /chat/.")

        # Сохраняем состояние сессии, чтобы не логиниться повторно
        #await self.page.context.storage_state(path="storage_state.json")
        #logger.info("Состояние сессии сохранено в storage_state.json.")

        return True
