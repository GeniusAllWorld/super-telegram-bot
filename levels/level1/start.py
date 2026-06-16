from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from sqlalchemy import select

from config import ADMIN_ID
from keyboards.main_menu import get_main_menu
from database.db import async_session_maker
from database.models import User

router = Router()

# Хэндлер команды /start с проверкой прав доступа и автоматической регистрацией
@router.message(CommandStart())
async def cmd_start(message: Message):
    # Если зашел главный админ — пускаем сразу без проверок БД
    if message.from_user.id == ADMIN_ID:
        await message.answer("👋 Привет, Главный Администратор!", reply_markup=get_main_menu())
        return

    # Открываем асинхронную сессию к базе данных
    async with async_session_maker() as session:
        query = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        # Если пользователя вообще нет в базе — автоматически регистрируем его (закрытый доступ)
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                is_whitelisted=False  # По умолчанию доступ закрыт, пока админ не одобрит
            )
            session.add(user)
            await session.commit()
            
        # Если пользователь зарегистрирован, но не активирован в белом списке — стопаем
        if not user.is_whitelisted:
            await message.answer(
                f"🛑 <b>Доступ ограничен!</b>\n\n"
                f"Ваш аккаунт зарегистрирован в системе.\n"
                f"Передайте ваш ID администратору для активации:\n"
                f"🆔 ID: <code>{message.from_user.id}</code>",
                parse_mode="HTML"
            )
            return

    # Если пользователь есть в белом списке — отдаем меню
    await message.answer(
        "👋 Привет! Я — Genius бот. Моя система верифицирована.\n"
        "Выберите интересующий вас уровень утилит на клавиатуре ниже:", 
        reply_markup=get_main_menu()
    )