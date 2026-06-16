import asyncio
import translators as ts
from aiogram import Router, F, html
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level2States

router = Router()


# Хэндлер инициализации переводчика текста
@router.callback_query(F.data == "cmd_translator")
async def start_translator(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🔤 <b>Переводчик текста</b>\n\n"
        "Отправьте мне любой текст или фразу на иностранном языке, и я переведу её на русский.\n"
        "Для выхода из режима отправьте слово <b>отмена</b>.",
        parse_mode="HTML"
    )
    await state.set_state(Level2States.waiting_for_translate_text)
    await callback.answer()


# Хэндлер асинхронного перевода текста через сторонний движок
@router.message(Level2States.waiting_for_translate_text)
async def process_translation(message: Message, state: FSMContext):
    text_to_translate = message.text.strip()
    
    # Обработка ручной отмены операции
    if text_to_translate.lower() in ["отмена", "/cancel"]:
        await state.clear()
        await message.answer("❌ Перевод отменен.")
        return
        
    # Защита от слишком длинного текста (ограничение Telegram на отправку сообщений)
    if len(text_to_translate) > 3000:
        await message.answer("❌ Текст слишком длинный! Пожалуйста, отправьте текст объемом до 3000 символов.")
        return
        
    # Показываем плашку "typing..." в интерфейсе Telegram
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        # Выполняем синхронную сетевую задачу в отдельном неблокирующем потоке (to_thread)
        translated_text = await asyncio.to_thread(
            ts.translate_text, 
            query_text=text_to_translate, 
            from_language='auto',  # Автоопределение исходного языка
            to_language='ru', 
            engine='bing'          # Стабильный движок Bing
        )
        
        # Пофиксили баг разметки: экранируем спецсимволы в переведенном тексте
        safe_translated_text = html.quote(translated_text)
        
        await message.answer(
            f"📋 <b>Результат перевода:</b>\n\n"
            f"<code>{safe_translated_text}</code>",
            parse_mode="HTML"
        )
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Не удалось выполнить перевод. Ошибка: {e}")
        await state.clear()