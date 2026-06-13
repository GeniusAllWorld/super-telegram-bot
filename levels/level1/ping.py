import time
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("ping"))
async def cmd_ping(message: Message):
    # Засекаем время начала
    start_time = time.perf_counter()
    
    # Отправляем временное сообщение, чтобы замерить отклик
    sent_message = await message.answer("🏓 Понг!")
    
    # Засекаем время конца
    end_time = time.perf_counter()
    
    # Вычисляем разницу в миллисекундах
    latency = (end_time - start_time) * 1000
    
    # Редактируем сообщение, показывая результат
    await sent_message.edit_text(f"🏓 Понг!\nЗадержка: <code>{latency:.2f} мс</code>", parse_mode="HTML")