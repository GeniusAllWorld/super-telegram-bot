from aiogram import Router, html
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

# Хэндлер вывода подробной диагностической информации о профиле пользователя
@router.message(Command("userinfo"))
async def cmd_userinfo(message: Message):
    user = message.from_user
    
    # Безопасно экранируем имя пользователя, чтобы избежать падения бота от символов < > & в никнейме
    full_name = html.quote(user.full_name)
    
    # Формируем юзернейм с проверкой на его существование
    username = f"@{user.username}" if user.username else "Отсутствует"
    user_id = user.id
    
    # Проверяем наличие Telegram Premium статуса
    is_premium = "Да 🔥" if user.is_premium else "Нет"
    
    # Получаем языковой код интерфейса приложения
    lang = user.language_code or "Не определен"
    
    # Собираем итоговый текст ответа в HTML-формате
    info_text = (
        "<b>📋 Карточка пользователя системы:</b>\n\n"
        f"👤 <b>Имя:</b> {full_name}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"💎 <b>Premium:</b> {is_premium}\n"
        f"🌐 <b>Язык:</b> {lang}"
    )
    
    await message.answer(info_text, parse_mode="HTML")