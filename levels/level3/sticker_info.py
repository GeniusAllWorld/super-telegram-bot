from aiogram import Router, F, html # Импортируем html для безопасного экранирования
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level3States

router = Router()


# Хэндлер инициализации запроса информации о стикер-паке
@router.callback_query(F.data == "cmd_sticker_info")
async def start_sticker_info(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🖼 <b>Анализатор стикер-паков</b>\n\n"
        "Пришлите мне любой стикер из пака, чтобы узнать информацию о нём!\n"
        "Для отмены операции напишите <b>отмена</b>.",
        parse_mode="HTML"
    )
    await state.set_state(Level3States.waiting_for_sticker)
    await callback.answer()


# Хэндлер обработки валидного стикера и получения данных через Telegram API
@router.message(Level3States.waiting_for_sticker, F.sticker)
async def process_sticker_info(message: Message, state: FSMContext):
    # Получаем техническое имя-идентификатор пака
    sticker_set_name = message.sticker.set_name
    
    if not sticker_set_name:
        await message.answer("❌ Этот стикер является одиночным (custom emoji) или не входит ни в один официальный пак.")
        await state.clear()
        return

    try:
        # Включаем экшен отправки текста, показывая работу бота
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        
        # Запрашиваем полный объект StickerSet у серверов Telegram
        sticker_set = await message.bot.get_sticker_set(name=sticker_set_name)
        
        # ПОФИКСИЛИ HTML-ИНЪЕКЦИЮ: Безопасно экранируем кастомные заголовки создателей паков
        title = html.quote(sticker_set.title)
        count = len(sticker_set.stickers)
        name = html.quote(sticker_set.name)
        
        # Формируем итоговую карточку параметров пака
        info = (
            f"📋 <b>Информация о стикер-паке:</b>\n\n"
            f"🔸 <b>Название:</b> {title}\n"
            f"🔸 <b>Кол-во стикеров:</b> {count}\n"
            f"🔸 <b>ID пака:</b> <code>{name}</code>\n"
        )
        
        await message.answer(info, parse_mode="HTML")
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Не удалось загрузить данные о паке от Telegram. Ошибка: {e}")
        await state.clear()


# ПОФИКСИЛИ ЗАВИСАНИЕ СТЕЙТА: Хэндлер перехвата невалидных типов данных или отмены
@router.message(Level3States.waiting_for_sticker)
async def process_sticker_info_invalid(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    
    # Обработка ручной отмены операции
    if text.lower() in ["отмена", "/cancel"]:
        await state.clear()
        await message.answer("❌ Сбор информации о стикере отменен.")
        return
        
    # Если юзер прислал текст или картинку вместо стикера, мягко возвращаем его на путь истинный
    await message.answer("❌ Это не стикер! Пожалуйста, пришлите именно <b>стикер</b> или напишите <b>отмена</b>.", parse_mode="HTML")