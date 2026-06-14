from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_level3_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Список методов Уровня 3
    buttons = [
        ("🎞 Поиск GIF", "cmd_gif_search"),
        ("🧩 Викторина", "cmd_quiz"),
        ("🖼 Генератор мемов", "cmd_meme_gen"),
        ("📝 Анализ текста", "cmd_text_analyze"),
        ("✊✋✌️ Камень-Ножницы-Бумага", "cmd_rps_game"),
        ("💬 Цитата дня", "cmd_quote"),
        ("📖 Википедия", "cmd_wiki"),
        ("🎧 Видео в аудио", "cmd_video_to_audio"),
        ("🏷 Инфо о стикерах", "cmd_sticker_info"),
        ("✨ Генератор имен", "cmd_name_gen")
    ]
    
    # Расставляем кнопки по 2 в ряд, чтобы меню не было бесконечно длинным
    for i in range(0, len(buttons), 2):
        row = []
        for text, callback in buttons[i:i+2]:
            row.append(InlineKeyboardButton(text=text, callback_data=callback))
        builder.row(*row)
        
    return builder.as_markup()