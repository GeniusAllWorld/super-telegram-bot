import json
import random
from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()

@router.callback_query(F.data == "cmd_quote")
async def send_quote(callback: CallbackQuery):
    try:
        # Читаем цитаты из нашего JSON файла
        with open("data/quotes.json", "r", encoding="utf-8") as file:
            quotes = json.load(file)
            
        quote = random.choice(quotes)
        
        await callback.message.answer(
            f"💡 <b>Цитата дня:</b>\n\n"
            f"<i>«{quote}»</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.message.answer("❌ Не удалось найти цитаты в базе данных.")
    
    await callback.answer()