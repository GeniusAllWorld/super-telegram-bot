from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime, timezone, timedelta

router = Router()

# Список часовых поясов со смещением в часах относительно UTC (актуально на лето 2026)
TIMEZONES = [
    ("London (UK)", 1),        # UTC+1
    ("Moscow (Russia)", 3),    # UTC+3
    ("Berlin (Germany)", 2),   # UTC+2
    ("Mumbai (India)", 5.5),   # UTC+5:30
    ("Beijing (China)", 8),    # UTC+8
    ("Tokyo (Japan)", 9),      # UTC+9
    ("New York (USA)", -4),    # UTC-4
    ("Los Angeles (USA)", -7), # UTC-7
    ("Cairo (Egypt)", 2),      # UTC+2
    ("Sydney (Australia)", 10) # UTC+10
]


# Хэндлер вывода текущего времени в ключевых мегаполисах мира
@router.message(Command("time"))
async def cmd_time(message: Message):
    # Получаем текущую точку времени в UTC
    now_utc = datetime.now(timezone.utc)
    
    result = ["<b>🕒 Текущее время по часовым поясам:</b>\n"]
    
    for label, offset in TIMEZONES:
        # Безопасный расчет: переводим всё смещение целиком в минуты.
        # Это полностью исключает баги округления int() при работе с отрицательными значениями.
        total_minutes = int(offset * 60)
        
        # Применяем смещение через timedelta
        target_time = now_utc + timedelta(minutes=total_minutes)
        formatted_time = target_time.strftime("%H:%M")
        
        # Формируем красивую строчку для вывода
        result.append(f"• {label}: <code>{formatted_time}</code>")
    
    # Склеиваем список в один текст и отправляем пользователю
    await message.answer("\n".join(result), parse_mode="HTML")