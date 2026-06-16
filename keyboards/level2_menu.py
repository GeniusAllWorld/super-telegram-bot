from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_level2_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Список утилит уровня: (текст кнопки, callback_data)
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
        ("+ Калькулятор", "cmd_calculator"),
    ]
    
    # Добавляем кнопки всех инструментов в билдер
    for text, callback in buttons:
        builder.add(InlineKeyboardButton(text=text, callback_data=callback))
        
    # Выстраиваем инструменты аккуратной сеткой по 2 штуки в ряд
    builder.adjust(2)
    
    # Кнопку возврата крепим отдельной строкой в самом низу
    builder.row(InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main"))
        
    return builder.as_markup()