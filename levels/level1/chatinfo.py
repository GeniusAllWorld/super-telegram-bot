from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest

router = Router()

@router.message(Command("chatinfo"))
async def cmd_chatinfo(message: Message):
    # ID чата доступен всегда
    chat_id = message.chat.id
    
    try:
        # Пытаемся получить количество участников
        count = await message.bot.get_chat_member_count(chat_id)
        info = f"👥 <b>Количество участников:</b> {count}"
    except TelegramBadRequest:
        # Если это личка, бот вызовет исключение, обрабатываем его
        info = "👤 <b>Тип чата:</b> Личное сообщение (участников: 1)"

    await message.answer(
        f"📋 <b>Информация о чате:</b>\n\n"
        f"🆔 <b>Chat ID:</b> <code>{chat_id}</code>\n"
        f"{info}",
        parse_mode="HTML"
    )