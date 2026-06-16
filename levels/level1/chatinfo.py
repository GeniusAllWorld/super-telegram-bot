from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

# Хэндлер сбора и вывода технической информации о текущем чате
@router.message(Command("chatinfo"))
async def cmd_chatinfo(message: Message):
    chat_id = message.chat.id
    chat_type = message.chat.type
    
    # Проверяем тип чата напрямую через свойства объекта Chat, избегая вызова исключений
    if chat_type == "private":
        chat_name = message.chat.full_name
        info = f"👤 <b>Тип чата:</b> Личный диалог\n" \
               f"📝 <b>Имя собеседника:</b> {chat_name}"
    else:
        chat_title = message.chat.title
        # Получаем количество участников асинхронно только для групп/каналов
        count = await message.bot.get_chat_member_count(chat_id)
        
        # Проверяем наличие публичной ссылки у чата
        username_str = f"🔗 <b>Username:</b> @{message.chat.username}\n" if message.chat.username else ""
        
        info = f"👥 <b>Тип чата:</b> Группа/Супергруппа ({chat_type})\n" \
               f"🏷 <b>Название:</b> {chat_title}\n" \
               f"{username_str}" \
               f"📊 <b>Участников:</b> {count}"

    # Отправляем итоговую сводку пользователю в HTML-формате
    await message.answer(
        f"📋 <b>Информация о чате:</b>\n\n"
        f"🆔 <b>Chat ID:</b> <code>{chat_id}</code>\n"
        f"{info}",
        parse_mode="HTML"
    )