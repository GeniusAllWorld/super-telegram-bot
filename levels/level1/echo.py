from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import StateFilter # Импортируем правильный фильтр состояний для aiogram 3.x

router = Router()

# Хэндлер безопасного Эхо-режима.
# Передаем StateFilter(None) вместо устаревшего свойства state=None.
@router.message(~F.text.startswith("/"), F.text, StateFilter(None))
async def echo_handler(message: Message):
    # Метод copy_to копирует сообщения обратно в чат со всеми медиа данными
    try:
        await message.copy_to(chat_id=message.chat.id)
    except Exception:
        # Защита от непредвиденных падений при отправке неподдерживаемых типов данных
        pass