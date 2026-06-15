from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_level4_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Список методов Уровня 4
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
        ("⏰ Планировщик задач", "cmd_cron_scheduler")
    ]
    
    # Расставляем красиво по 2 в ряд
    for i in range(0, len(buttons), 2):
        row = []
        for text, callback in buttons[i:i+2]:
            row.append(InlineKeyboardButton(text=text, callback_data=callback))
        builder.row(*row)
        
    return builder.as_markup()