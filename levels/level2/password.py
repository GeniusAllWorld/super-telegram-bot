import secrets
import string
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

# Хэндлер криптографически безопасной генерации сложных паролей
@router.callback_query(F.data == "cmd_password")
async def generate_password_handler(callback: CallbackQuery):
    # Гарантируем высокую надежность: увеличиваем длину до 12 символов (стандарт безопасности)
    password_length = 12
    
    # Списки обязательных символов для выполнения требований к сложности
    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    digits = string.digits
    special = "!@#$%^&*"
    
    # Собираем гарантированный базис (минимум по одному символу каждого типа)
    password_base = [
        secrets.choice(lower),
        secrets.choice(upper),
        secrets.choice(digits),
        secrets.choice(special)
    ]
    
    # Оставшиеся символы добираем из полного алфавита
    all_characters = lower + upper + digits + special
    password_remain = [secrets.choice(all_characters) for _ in range(password_length - len(password_base))]
    
    # Объединяем списки и перемешиваем криптографически безопасным методом
    full_password_list = password_base + password_remain
    secrets.SystemRandom().shuffle(full_password_list)
    password = "".join(full_password_list)
    
    # Создаем инлайн-клавиатуру для мгновенной перегенерации
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Сгенерировать еще раз", callback_data="cmd_password")
    
    text = (
        f"🔑 <b>Ваш надежный пароль ({password_length} символов):</b>\n\n"
        f"<code>{password}</code>\n\n"
        f"<i>💡 Нажмите на пароль, чтобы мгновенно скопировать его.</i>"
    )
    
    # Пофиксили UX: изменяем текст текущего сообщения, чтобы не засорять историю чата
    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
    except Exception:
        # Игнорируем ошибку Telegram, если случайно сгенерировался точно такой же пароль (шанс ничтожно мал)
        pass
        
    # Гасим индикатор загрузки инлайн-кнопки
    await callback.answer()