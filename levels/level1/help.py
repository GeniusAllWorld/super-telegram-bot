from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

# Наш список команд с кратким описанием
COMMANDS = {
    "/start": "Приветствие и описание возможностей",
    "/help": "Список всех команд",
    "/ping": "Проверка задержки отклика бота",
    "/userinfo": "Твои данные: ID, имя, юзернейм",
    "/time": "Текущее время в разных поясах",
    "/chatinfo": "Информация о чате",
    "/avatar": "Установить фото профиля бота",
    "/version": "Текущая версия бота",
    "/exit": "Удаление бота из чата"
}

@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = "<b>Список доступных команд:</b>\n\n"
    for cmd, desc in COMMANDS.items():
        help_text += f"{cmd} — {desc}\n"
    
    await message.answer(help_text + "/start - для выбора уровня", parse_mode="HTML")