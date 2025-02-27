# bot/telegram_bot.py

import asyncio
from telegram import Update, Message
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from utils.logger import logger

from steam.login import SteamLogin
from steam.screenshot import make_screenshot

steam_session: SteamLogin | None = None
bot_messages: list[int] = []

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global bot_messages
    # Удаляем все сообщения бота при запуске /start
    for msg_id in bot_messages:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg_id)
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщения {msg_id}: {e}")
    bot_messages.clear()

    logger.debug("Вызвана команда /start")
    await update.message.reply_text(
        "Привет! Я бот для работы со Steam (Playwright, async).\n"
        "Доступные команды:\n"
        "/loginsteam - запуск логина\n"
        "/checkstatus - проверить статус\n"
        "/sendrandomfriendmsgadvanced <текст> - отправить сообщение случайному другу\n"
        "/clearchat - очистить сообщения бота"
    )

async def login_steam_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global steam_session, bot_messages
    logger.info("Запуск Playwright (async) для Steam через /loginsteam")

    if steam_session and await steam_session.is_logged_in():
        await update.message.reply_text("Уже залогинены в Steam, повторный вход не требуется.")
        return

    if not steam_session:
        steam_session = SteamLogin(headless=True)
    await steam_session.open_steam_login_page()
    await asyncio.sleep(4)

    old_message: Message | None = None
    try:
        while True:
            if await steam_session.is_logged_in():
                await update.message.reply_text("Вход успешно завершён!")
                break

            screenshot_path = "screenshots/steam_login.png"
            success = await make_screenshot(steam_session.page, screenshot_path)
            if success:
                new_msg = await update.message.reply_photo(open(screenshot_path, "rb"))
                bot_messages.append(new_msg.message_id)
                if old_message is not None:
                    try:
                        await context.bot.delete_message(
                            chat_id=update.effective_chat.id,
                            message_id=old_message.message_id
                        )
                    except Exception as e:
                        logger.error(f"Ошибка при удалении старого сообщения: {e}")
                old_message = new_msg
            else:
                await update.message.reply_text("Не удалось сделать скриншот (Playwright async).")
            await asyncio.sleep(2)
    except Exception as e:
        logger.error(f"Ошибка в цикле скриншотов: {e}")
    finally:
        logger.info("Цикл логина завершён (или уже авторизовались).")

async def check_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global steam_session
    if not steam_session:
        await update.message.reply_text("Нет активной сессии Steam. Используй /loginsteam для входа.")
        return
    if await steam_session.is_logged_in():
        await update.message.reply_text("Уже залогинены в Steam! Можно использовать команды.")
    else:
        await update.message.reply_text("Сессия есть, но не авторизована. Используй /loginsteam заново.")

async def send_random_friend_message_advanced_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global steam_session, bot_messages
    logger.info("Вызвана команда /sendrandomfriendmsgadvanced")

    if not steam_session:
        await update.message.reply_text("Сессия Steam отсутствует. Сначала /loginsteam.")
        return
    if not await steam_session.is_logged_in():
        await update.message.reply_text("Вы не залогинены! Сначала используйте /loginsteam.")
        return

    msg_text = " ".join(context.args).strip()
    if not msg_text:
        msg_text = "Hello from Steam Bot (advanced)!"

    success = await steam_session.send_random_friend_message_advanced(msg_text)
    if not success:
        await update.message.reply_text("Не удалось отправить сообщение. Проверьте наличие друзей или селекторы.")
        return

    screenshot_path = "screenshots/send_friend_msg.png"
    shot_ok = await make_screenshot(steam_session.page, screenshot_path)
    if shot_ok:
        try:
            new_msg = await update.message.reply_photo(open(screenshot_path, "rb"))
            bot_messages.append(new_msg.message_id)
        except Exception as e:
            logger.error(f"Ошибка при отправке скриншота: {e}")
    else:
        await update.message.reply_text("Не удалось сделать скриншот после отправки.")

async def clear_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global bot_messages
    deleted = 0
    for msg_id in bot_messages:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg_id)
            deleted += 1
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщения {msg_id}: {e}")
    bot_messages.clear()
    await update.message.reply_text(f"Удалено сообщений: {deleted}")

def run_bot(token: str):
    logger.info("Инициализация Telegram-бота (Playwright-async-версия)...")
    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("loginsteam", login_steam_command))
    application.add_handler(CommandHandler("checkstatus", check_status_command))
    application.add_handler(CommandHandler("sendrandomfriendmsgadvanced", send_random_friend_message_advanced_command))
    application.add_handler(CommandHandler("clearchat", clear_chat_command))

    logger.info("Обработчики /start, /loginsteam, /checkstatus, /sendrandomfriendmsgadvanced, /clearchat зарегистрированы.")
    application.run_polling(drop_pending_updates=True)
    logger.info("Бот остановлен.")
