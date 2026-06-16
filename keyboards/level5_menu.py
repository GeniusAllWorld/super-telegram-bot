import random
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import WEBAPP_URL


def get_level5_keyboard() -> InlineKeyboardMarkup:
    # Защита: если URL веб-приложения не задан в конфигурации, ставим заглушку
    base_url = WEBAPP_URL or "https://telegram.org"

    # Генерируем случайное число, чтобы заставить Telegram каждый раз загружать свежую версию приложения
    cache_buster = random.randint(100000, 999999)
    
    # Корректно склеиваем URL в зависимости от того, есть ли уже GET-параметры в исходной ссылке
    separator = "&" if "?" in base_url else "?"
    updated_url = f"{base_url}{separator}v={cache_buster}"
    
    # Формируем клавиатуру напрямую (так как кнопок всего две, билдер здесь не обязателен)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚀 Запустить Sci-Fi Mini App",
                web_app=WebAppInfo(url=updated_url)
            )
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main")
        ]
    ])