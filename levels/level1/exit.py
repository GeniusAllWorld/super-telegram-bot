from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("exit"))
async def cmd_exit(message: Message):
    await message.answer("👋 Прощаюсь! Ухожу из этого чата.")
    # Бот покидает чат
    await message.bot.leave_chat(message.chat.id)