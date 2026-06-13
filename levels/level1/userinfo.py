from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("userinfo"))
async def cmd_userinfo(message: Message):
    user = message.from_user
    
    # Формируем данные
    full_name = user.full_name
    username = f"@{user.username}" if user.username else "Нет юзернейма"
    user_id = user.id
    is_premium = "Да" if user.is_premium else "Нет"
    lang = user.language_code or "Не определен"
    
    # Собираем красивый ответ
    info_text = (
        "<b>Информация о пользователе:</b>\n\n"
        f"👤 <b>Имя:</b> {full_name}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"💎 <b>Premium:</b> {is_premium}\n"
        f"🌐 <b>Язык:</b> {lang}"
    )
    
    await message.answer(info_text, parse_mode="HTML")