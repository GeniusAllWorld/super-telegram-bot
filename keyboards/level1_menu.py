from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_level1_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Список методов: (текст_кнопки, callback_data)
    buttons = [
        ("Start", "cmd_start"),
        ("Help", "cmd_help"),
        ("Echo", "cmd_echo"),
        ("Ping", "cmd_ping"),
        ("User Info", "cmd_userinfo"),
        ("Time", "cmd_time"),
        ("Chat Info", "cmd_chatinfo"),
        ("Avatar", "cmd_avatar"),
        ("Version", "cmd_version"),
        ("Exit", "cmd_exit")
    ]
    
    for text, callback in buttons:
        builder.row(InlineKeyboardButton(text=text, callback_data=callback))
    
    return builder.as_markup()