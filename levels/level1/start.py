from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from keyboards.main_menu import get_main_menu
from config import ADMIN_ID
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Привет, Админ!", reply_markup=get_main_menu())
        return

    async with async_session() as session:
        query = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        # Если юзера нет в базе или у него флаг False — стопаем его
        if not user or not user.is_whitelisted:
            await message.answer("🛑 <b>Доступ ограничен!</b>\nВы должны находиться в белом списке, чтобы использовать этого бота.")
            return

    await message.answer("Привет! Я — бот-безумие. Готов к работе. Выбери уровень:.", reply_markup=get_main_menu())