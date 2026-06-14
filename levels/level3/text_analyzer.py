from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level3States

router = Router()

@router.callback_query(F.data == "cmd_text_analyze")
async def start_analyzer(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📝 <b>Анализатор текста</b>\n\n"
        "Отправьте мне любой текст, и я посчитаю количество слов и символов в нем:",
        parse_mode="HTML"
    )
    await state.set_state(Level3States.waiting_for_text_to_analyze)
    await callback.answer()

@router.message(Level3States.waiting_for_text_to_analyze, F.text)
async def process_analyzer(message: Message, state: FSMContext):
    text = message.text
    
    # Считаем символы (включая пробелы)
    char_count = len(text)
    
    # Считаем слова (split по умолчанию делит по любым пробельным символам)
    words = text.split()
    word_count = len(words)
    
    await message.answer(
        f"📊 <b>Результаты анализа:</b>\n\n"
        f"🔹 Слов: <code>{word_count}</code>\n"
        f"🔹 Символов: <code>{char_count}</code>",
        parse_mode="HTML"
    )
    
    await state.clear()