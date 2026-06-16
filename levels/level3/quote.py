import json
import random
import os
from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()

# Путь к файлу с цитатами
QUOTES_FILE = os.path.join("data", "quotes.json")

# Кэш для хранения цитат в оперативной памяти (чтобы не читать диск при каждом клике)
_quotes_cache = []


def load_quotes_to_cache():
    global _quotes_cache
    # Если кэш уже заполнен, не читаем файл заново
    if _quotes_cache:
        return
        
    try:
        if os.path.exists(QUOTES_FILE):
            with open(QUOTES_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                # Поддерживаем как простой список строк, так и список словарей с авторами
                if isinstance(data, list):
                    _quotes_cache = data
                else:
                    _quotes_cache = []
        else:
            _quotes_cache = []
    except Exception as e:
        print(f"Ошибка предварительной загрузки цитат: {e}")
        _quotes_cache = []


# Хэндлер выдачи случайной цитаты из кэша памяти
@router.callback_query(F.data == "cmd_quote")
async def send_quote(callback: CallbackQuery):
    # Гарантируем, что кэш инициализирован
    load_quotes_to_cache()
    
    if not _quotes_cache:
        await callback.message.answer("❌ База данных цитат пуста или недоступна. Создайте файл data/quotes.json.")
        await callback.answer()
        return
        
    try:
        # Выбираем случайный элемент из кэша в ОЗУ — это происходит мгновенно
        item = random.choice(_quotes_cache)
        
        # Проверяем структуру элемента (строка или словарь с автором)
        if isinstance(item, dict):
            text = item.get("text", "Текст цитаты отсутствует.")
            author = item.get("author", "Неизвестный автор")
            quote_text = f"<i>«{text}»</i>\n\n✍️ <b>{author}</b>"
        else:
            # Обычная плоская строка
            quote_text = f"<i>«{item}»</i>"
            
        await callback.message.answer(
            f"💡 <b>Цитата дня:</b>\n\n{quote_text}",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await callback.message.answer(f"❌ Не удалось обработать цитату. Ошибка: {e}")
        
    await callback.answer()