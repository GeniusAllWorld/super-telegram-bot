from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime, timezone, timedelta

router = Router()

# Смещения относительно UTC в часах
TIMEZONES = [
    ("London (UK)", 1),        # UTC+1 (Лето)
    ("Moscow (Russia)", 3),    # UTC+3
    ("Berlin (Germany)", 2),   # UTC+2 (Лето)
    ("Mumbai (India)", 5.5),   # UTC+5:30
    ("Beijing (China)", 8),    # UTC+8
    ("Tokyo (Japan)", 9),      # UTC+9
    ("New York (USA)", -4),    # UTC-4 (Лето)
    ("Los Angeles (USA)", -7), # UTC-7 (Лето)
    ("Cairo (Egypt)", 2),      # UTC+2
    ("Sydney (Australia)", 10) # UTC+10
]

@router.message(Command("time"))
async def cmd_time(message: Message):
    # Берем "чистое" время UTC
    now_utc = datetime.now(timezone.utc)
    
    result = ["<b>🕒 Текущее время (UTC-базис):</b>\n"]
    
    for label, offset in TIMEZONES:
        # Добавляем смещение вручную через timedelta
        # Если смещение дробное (как 5.5), используем минуты
        hours = int(offset)
        minutes = int((offset - hours) * 60)
        
        target_time = now_utc + timedelta(hours=hours, minutes=minutes)
        t = target_time.strftime("%H:%M")
        result.append(f"• {label}: <code>{t}</code>")
    
    await message.answer("\n".join(result), parse_mode="HTML")