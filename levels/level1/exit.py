from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from config import ADMIN_ID

router = Router()

# Хэндлер экстренного выхода бота из группы (доступно только ADMIN_ID)
@router.message(Command("exit"))
async def cmd_exit(message: Message):
    # Жесткая проверка: только создатель/админ бота может управлять его присутствием
    if message.from_user.id != ADMIN_ID:
        return

    # Проверяем тип чата. Если это ЛС — выходить некуда, просто прощаемся
    if message.chat.type == "private":
        await message.answer("👋 Сессия закрыта! Для возобновления работы используйте /start.")
        return

    # Если это группа или супергруппа — отправляем уведомление и покидаем чат
    try:
        await message.answer("👋 Внимание! Администратор отозвал бота. Покидаю этот чат...")
        await message.bot.leave_chat(chat_id=message.chat.id)
    except Exception:
        # Защита от непредвиденных ошибок Telegram API при выходе
        pass