from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from config import BOT_VERSION, BUILD_DATE

router = Router()

@router.message(Command("version"))
async def cmd_version(message: Message):
    await message.answer(
        f"🤖 <b>Версия бота:</b> <code>{BOT_VERSION}</code>\n"
        f"📅 <b>Дата сборки:</b> {BUILD_DATE}\n\n"
        f"<i>Работаем над стабильностью!</i>",
        parse_mode="HTML"
    )