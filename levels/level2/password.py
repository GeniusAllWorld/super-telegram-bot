import secrets
import string
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

@router.callback_query(F.data == "cmd_password")
async def generate_password_handler(callback: CallbackQuery):
    # Набор символов: заглавные, строчные буквы, цифры и спецсимволы
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    
    # Криптографически безопасная генерация 8 символов
    password = "".join(secrets.choice(alphabet) for _ in range(8))
    
    # Создаем инлайн-кнопку, чтобы пользователь мог сгенерировать новый пароль, не выходя в меню
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Сгенерировать еще раз", callback_data="cmd_password")
    
    await callback.message.answer(
        f"🔑 <b>Ваш надежный пароль (8 символов):</b>\n\n"
        f"<code>{password}</code>\n\n"
        f"<i>💡 Нажмите на пароль, чтобы скопировать его.</i>",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    
    # Убираем анимацию загрузки на кнопке
    await callback.answer()