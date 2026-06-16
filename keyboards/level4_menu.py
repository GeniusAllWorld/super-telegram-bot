from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_level4_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Список инструментов разработчика: (текст кнопки, callback_data)
    buttons = [
        ("🐙 GitHub Инфо", "cmd_github_check"),
        ("🗄 SQL Консоль", "cmd_sql_console"),
        ("🐍 Запуск Python", "cmd_eval_code"),
        ("📊 Нагрузка сервера", "cmd_server_monitor"),
        ("🤖 ИИ Автоответчик", "cmd_ai_respond"),
        ("🎙 Голос в текст", "cmd_whisper_stt"),
        ("👁 Текст с фото (OCR)", "cmd_tesseract_ocr"),
        ("🛡 Антиспам фильтр", "cmd_antispam_config"),
        ("📝 Белый список (БД)", "cmd_whitelist_manager"),
        ("⏰ Планировщик задач", "cmd_cron_scheduler"),
    ]
    
    # Массово добавляем кнопки утилит в билдер
    for text, callback in buttons:
        builder.add(InlineKeyboardButton(text=text, callback_data=callback))
        
    # Выравниваем кнопки по 2 штуки в ряд
    builder.adjust(2)
    
    # Фиксируем навигацию на отдельной строке в самом низу
    builder.row(InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main"))
        
    return builder.as_markup()