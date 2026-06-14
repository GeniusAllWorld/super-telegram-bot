from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_level2_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Список методов Уровня 2: (текст_кнопки, callback_data)
    buttons = [
        ("🎲 Рандомайзер (1-N)", "cmd_random_num"),
        ("🔑 Генератор паролей", "cmd_password"),
        ("💱 Конвертер валют", "cmd_currency"),
        ("🌤 Погода в городе", "cmd_weather"),
        ("🔲 QR-код генератор", "cmd_qrcode_gen"),
        ("🔗 Сокращатель ссылок", "cmd_shortener"),
        ("⏳ Таймер (X минут)", "cmd_timer"),
        ("⏰ Будильник", "cmd_alarm"),
        ("🗣 Переводчик текста", "cmd_translator"),
        ("+ Калькулятор", "cmd_calculator")
    ]
    
    for i in range(0, len(buttons), 2):
        row = []
        for text, callback in buttons[i:i+2]:
            row.append(InlineKeyboardButton(text=text, callback_data=callback))
        builder.row(*row)
        
    return builder.as_markup()