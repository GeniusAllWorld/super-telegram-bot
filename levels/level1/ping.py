import time
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

# Хэндлер замера сетевой задержки (RTT) между сервером бота и Telegram API
@router.message(Command("ping"))
async def cmd_ping(message: Message):
    # Фиксируем высокоточную временную метку до отправки запроса
    start_time = time.perf_counter()
    
    # Отправляем первичный пакет-сообщение в Telegram
    sent_message = await message.answer("🏓 Замеряю отклик...")
    
    # Фиксируем временную метку сразу после возвращения ответа от API
    end_time = time.perf_counter()
    
    # Вычисляем чистую задержку в миллисекундах
    latency = (end_time - start_time) * 1000
    
    # Определяем статус качества соединения на основе пинга
    if latency < 150:
        status = "🟢 Отлично"
    elif latency < 350:
        status = "🟡 Нормально"
    else:
        status = "🔴 Высокая задержка"
    
    # Обновляем отправленное сообщение итоговыми данными диагностики
    await sent_message.edit_text(
        f"🏓 <b>Понг!</b>\n\n"
        f"📡 <b>Соединение:</b> <code>{status}</code>\n"
        f"⚡ <b>Задержка API:</b> <code>{latency:.2f} мс</code>",
        parse_mode="HTML"
    )