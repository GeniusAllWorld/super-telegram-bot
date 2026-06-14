import asyncio
import translators as ts
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level2States

router = Router()

@router.callback_query(F.data == "cmd_translator")
async def start_translator(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🔤 <b>Переводчик текста</b>\n\n"
        "Отправьте мне любой текст или фразу на иностранном языке, и я переведу её на русский:",
        parse_mode="HTML"
    )
    await state.set_state(Level2States.waiting_for_translate_text)
    await callback.answer()


@router.message(Level2States.waiting_for_translate_text)
async def process_translation(message: Message, state: FSMContext):
    text_to_translate = message.text.strip()
    
    # Показываем плашку, что бот печатает перевод
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        # Переключаемся на движок bing и явно включаем автоопределение языка
        translated_text = await asyncio.to_thread(
            ts.translate_text, 
            query_text=text_to_translate, 
            from_language='auto', # Автодерект исходного языка
            to_language='ru', 
            engine='bing'         # Меняем google на bing
        )
        
        await message.answer(
            f"📋 <b>Результат перевода:</b>\n\n"
            f"<code>{translated_text}</code>",
            parse_mode="HTML"
        )
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Не удалось выполнить перевод. Ошибка: {e}")
        await state.clear()