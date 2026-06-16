from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_level3_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Список медиа и развлекательных функций уровня: (текст кнопки, callback_data)
    buttons = [
        ("🎞 Поиск GIF", "cmd_gif_search"),
        ("🧩 Викторина", "cmd_quiz"),
        ("🖼 Генератор мемов", "cmd_meme_gen"),
        ("📝 Анализ текста", "cmd_text_analyze"),
        ("✊✋✌️ Камень-Ножницы", "cmd_rps_game"),
        ("💬 Цитата дня", "cmd_quote"),
        ("📖 Википедия", "cmd_wiki"),
        ("🎧 Видео в аудио", "cmd_video_to_audio"),
        ("🏷 Инфо о стикерах", "cmd_sticker_info"),
        ("✨ Генератор имен", "cmd_name_gen"),
    ]
    
    # Заполняем билдер кнопками функций
    for text, callback in buttons:
        builder.add(InlineKeyboardButton(text=text, callback_data=callback))
        
    # Формируем сетку кнопок строго по парам
    builder.adjust(2)
    
    # Гарантированно выносим навигацию на отдельную строку в самый низ
    builder.row(InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main"))
        
    return builder.as_markup()