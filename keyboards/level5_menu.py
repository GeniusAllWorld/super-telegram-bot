import os
import random
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import WEBAPP_URL

def get_level5_keyboard() -> InlineKeyboardMarkup:
    # Генерируем случайное число, чтобы обмануть кэш браузера Телеграма
    cache_buster = random.randint(100000, 999999)
    # Наша ссылка теперь будет выглядеть как https://xyz.ngrok-free.dev/?v=123456
    updated_url = f"{WEBAPP_URL}/?v={cache_buster}" if "?" not in WEBAPP_URL else f"{WEBAPP_URL}&v={cache_buster}"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚀 Запустить Sci-Fi Mini App",
                web_app=WebAppInfo(url=updated_url)  # Ссылка со сбросом кэша
            )
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main")
        ]
    ])