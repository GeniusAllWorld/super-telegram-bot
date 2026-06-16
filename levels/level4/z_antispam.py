import os
import re
import html # Импортируем html для безопасного форматирования имен нарушителей
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest
from config import ADMIN_ID

router = Router()

# Список запрещенных слов (нижний регистр)
BAD_WORDS = ["скам", "крипта", "заработок", "бабки", "казино", "ставки", "vulkan"]

# Регулярное выражение для поиска ссылок и юзернеймов/инвайтов
URL_PATTERN = re.compile(
    r'(https?://[^\s]+)|(www\.[^\s]+)|(t\.me/[^\s]+)', 
    re.IGNORECASE
)


# 1. Информационное окно антиспама в админ-меню
@router.callback_query(F.data == "cmd_antispam_config")
async def antispam_info_btn(callback: CallbackQuery):
    # Проверка на главного разработчика/администратора
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return

    await callback.message.answer(
        "🛡 <b>Авто-удаление спама</b>\n\n"
        "Эта функция работает автоматически в группах и супергруппах!\n"
        "Просто добавьте бота в чат и выдайте ему права на <b>Удаление сообщений</b>. 🤖",
        parse_mode="HTML"
    )
    await callback.answer()


# 2. Фоновый модератор: обрабатывает сообщения ТОЛЬКО в чатах, исключая личку
@router.message(F.chat.type.in_({"group", "supergroup"}), F.text)
async def filter_group_messages(message: Message):
    # ПОФИКСИЛИ БЕСКОНЕЧНЫЙ ЦИКЛ: Если сообщение прислал любой бот (включая этого), полностью игнорируем его
    if message.from_user.is_bot:
        return

    # Если пишет создатель бота, отключаем для него фильтрацию
    if message.from_user.id == ADMIN_ID:
        return

    text_lower = message.text.lower()
    is_spam = False
    reason = ""

    # Анализируем текст на наличие внешних ссылок
    if URL_PATTERN.search(text_lower):
        is_spam = True
        reason = "размещение ссылок"

    # Анализируем текст на стоп-слова
    if not is_spam:
        for word in BAD_WORDS:
            if word in text_lower:
                is_spam = True
                reason = f"использование запрещенного слова"
                break

    # Если триггер сработал — уничтожаем спам-контент
    if is_spam:
        try:
            # Сначала удаляем запрещенное сообщение
            await message.delete()
            
            # ПОФИКСИЛИ HTML-ИНЪЕКЦИЮ: Безопасно формируем упоминание, экранируя full_name нарушителя
            if message.from_user.username:
                user_mention = f"@{html.quote(message.from_user.username)}"
            else:
                user_mention = f"<b>{html.quote(message.from_user.full_name)}</b>"
            
            # Отправляем предупреждение (в тексте больше нет уязвимого динамического {word}, вызывающего петлю)
            await message.answer(
                f"⚠️ <b>Антиспам модератор</b>\n"
                f"Сообщение от {user_mention} удалено.\n"
                f"❌ Нарушение: {reason}."
                f"Парсинг стоп-слов заблокирован.",
                parse_mode="HTML"
            )
        except TelegramBadRequest:
            # Защита на случай, если бота добавили в группу без прав удаления сообщений
            pass