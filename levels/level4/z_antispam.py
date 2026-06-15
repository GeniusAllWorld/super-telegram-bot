import os
import re
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest
from config import ADMIN_ID

router = Router()

# Список запрещенных слов
BAD_WORDS = ["скам", "крипта", "заработок", "бабки", "казино", "ставки", "vulkan"]

# Регулярка для поиска ссылок
URL_PATTERN = re.compile(
    r'(https?://[^\s]+)|(www\.[^\s]+)|(t\.me/[^\s]+)', 
    re.IGNORECASE
)

# 1. Срабатывает при нажатии на кнопку в админ-меню бота
@router.callback_query(F.data == "cmd_antispam")
async def antispam_info_btn(callback: CallbackQuery):
    # Традиционная проверка на админа для кнопки
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return

    await callback.message.answer(
        "🛡 <b>Авто-удаление спама</b>\n\n"
        "Эта функция работает только в группах!\n"
        "Она автоматическая, просто добавьте бота в группу и дайте ему права Админа! 🤖",
        parse_mode="HTML"
    )
    await callback.answer()


# 2. Фоновый хендлер: работает ТОЛЬКО в группах и супергруппах
@router.message(F.chat.type.in_({"group", "supergroup"}), F.text)
async def filter_group_messages(message: Message):
    # Если это пишет создатель бота (админ), игнорируем проверку
    if message.from_user.id == ADMIN_ID:
        return

    text_lower = message.text.lower()
    is_spam = False
    reason = ""

    # Проверяем ссылки
    if URL_PATTERN.search(text_lower):
        is_spam = True
        reason = "размещение ссылок"

    # Проверяем ключевые слова
    if not is_spam:
        for word in BAD_WORDS:
            if word in text_lower:
                is_spam = True
                reason = f"использование запрещенного слова '{word}'"
                break

    # Если нашли спам — удаляем
    if is_spam:
        try:
            await message.delete()
            
            # Тегаем спамера (если есть юзернейм) или пишем его имя
            user_mention = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
            
            await message.answer(
                f"⚠️ <b>Антиспам модератор</b>\n"
                f"Сообщение от {user_mention} удалено.\n"
                f"❌ Нарушение: {reason}."
            )
        except TelegramBadRequest:
            # Сработает, если бота в группу добавили, а админку дать забыли
            await message.answer("⚠️ Я вижу спам, но не могу его удалить! Дайте мне права Администратора.")