from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import ADMIN_ID
from utils.states import Level1States

router = Router()

# Хэндлер инициации смены аватарки группы (доступ только для ADMIN_ID)
@router.message(Command("avatar"))
async def cmd_avatar(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    # Проверяем, что команда вызвана в группе, а не в личке
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("❌ Эта команда работает только внутри групп или супергрупп!")
        return
        
    await state.set_state(Level1States.waiting_for_photo)
    await message.answer("📸 Пришли фото, я установлю его на аватарку этой группы.")

# Хэндлер обработки полученного фото и обновления аватарки чата
@router.message(Level1States.waiting_for_photo, F.photo)
async def set_avatar(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    downloaded_file = await message.bot.download_file(file.file_path)
    
    try:
        # Исправлено: используем .getvalue() для извлечения сырых байт из BytesIO
        await message.bot.set_chat_photo(
            chat_id=message.chat.id, 
            photo=BufferedInputFile(downloaded_file.getvalue(), filename="avatar.jpg")
        )
        await message.answer("✅ Аватарка группы успешно обновлена!")
    except Exception as e:
        await message.answer(f"❌ Не удалось обновить аватарку. Ошибка: {e}")
    finally:
        await state.clear()

# Хэндлер-заглушка на случай, если вместо фото админ прислал текст или другой объект
@router.message(Level1States.waiting_for_photo)
async def avatar_invalid_content(message: Message, state: FSMContext):
    if message.text and message.text.lower() in ["отмена", "/cancel"]:
        await state.clear()
        await message.answer("❌ Действие отменено.")
        return
    await message.answer("⚠ Пожалуйста, отправьте именно **фотографию**, либо напишите 'отмена' для выхода.")