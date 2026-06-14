from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level3States

router = Router()

@router.callback_query(F.data == "cmd_sticker_info")
async def start_sticker_info(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🖼 Пришли мне любой стикер из пака, чтобы узнать информацию о нём!")
    await state.set_state(Level3States.waiting_for_sticker)
    await callback.answer()

@router.message(Level3States.waiting_for_sticker, F.sticker)
async def process_sticker_info(message: Message, state: FSMContext):
    # 1. Получаем имя стикер-пака (это просто строка-идентификатор)
    sticker_set_name = message.sticker.set_name
    
    if not sticker_set_name:
        await message.answer("❌ Этот стикер не входит ни в один пак.")
        await state.clear()
        return

    try:
        # 2. ВОТ ОН: запрашиваем объект у Telegram API по имени строки
        sticker_set = await message.bot.get_sticker_set(name=sticker_set_name)
        
        # 3. Теперь вытаскиваем свойства из реального объекта StickerSet
        title = sticker_set.title
        count = len(sticker_set.stickers)
        name = sticker_set.name
        
        info = (
            f"📋 <b>Информация о стикер-паке:</b>\n\n"
            f"🔸 <b>Название:</b> {title}\n"
            f"🔸 <b>Кол-во стикеров:</b> {count}\n"
            f"🔸 <b>ID пака:</b> <code>{name}</code>\n"
        )
        
        await message.answer(info, parse_mode="HTML")
        
    except Exception as e:
        await message.answer(f"❌ Не удалось загрузить данные о паке от Telegram. Ошибка: {e}")
        
    await state.clear()