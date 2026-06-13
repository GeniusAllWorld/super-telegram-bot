from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from keyboards.main_menu import get_main_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Я — бот-безумие. Готов к работе. Выбери уровень:.", reply_markup=get_main_menu())