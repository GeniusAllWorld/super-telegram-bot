from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import ADMIN_ID
from utils.states import Level1States # импортируй из своего файла

router = Router()

@router.message(Command("avatar"))
async def cmd_avatar(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    await state.set_state(Level1States.waiting_for_photo)
    await message.answer("📸 Пришли фото, я установлю его на аватарку группы.")

@router.message(Level1States.waiting_for_photo, F.photo)
async def set_avatar(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    downloaded_file = await message.bot.download_file(file.file_path)
    
    try:
        await message.bot.set_chat_photo(
            chat_id=message.chat.id, 
            photo=BufferedInputFile(downloaded_file.read(), filename="avatar.jpg")
        )
        await message.answer("✅ Аватарка обновлена!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    finally:
        await state.clear() # Выходим из состояния