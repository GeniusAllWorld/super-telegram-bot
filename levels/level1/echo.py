from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from levels.level1.avatar import AvatarStates # Импортируем состояния

router = Router()

'''@router.message(~F.text.startswith("/"))
async def echo_handler(message: Message, state: FSMContext):
    # Получаем текущее состояние
    current_state = await state.get_state()
    
    #await message.copy_to(chat_id=message.chat.id)'''