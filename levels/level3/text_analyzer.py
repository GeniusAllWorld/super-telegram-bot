from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level3States

router = Router()


# Хэндлер инициализации анализатора текста
@router.callback_query(F.data == "cmd_text_analyze")
async def start_analyzer(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📝 <b>Анализатор текста</b>\n\n"
        "Отправьте мне любой текст (или перешлите пост), и я детально посчитаю количество слов и символов в нем.\n"
        "Для отмены операции напишите <b>отмена</b>.",
        parse_mode="HTML"
    )
    await state.set_state(Level3States.waiting_for_text_to_analyze)
    await callback.answer()


# Хэндлер основного анализа, поддерживающий обычный текст и подписи к медиафайлам
@router.message(Level3States.waiting_for_text_to_analyze, F.text | F.caption)
async def process_analyzer(message: Message, state: FSMContext):
    # Извлекаем текст как из обычного сообщения, так и из описания к картинке/видео
    target_text = message.text if message.text else message.caption
    target_text = target_text.strip()
    
    # Обработка ручной отмены операции
    if target_text.lower() in ["отмена", "/cancel"]:
        await state.clear()
        await message.answer("❌ Анализ текста отменен.")
        return
        
    # Включаем имитацию набора текста
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # Считаем общее количество символов (включая пробелы и переносы)
    total_chars = len(target_text)
    
    # Прокачиваем метрику: считаем чистые символы без пробельных знаков
    chars_no_spaces = len(target_text.replace(" ", "").replace("\n", "").replace("\r", ""))
    
    # Разбираем текст на массив слов (split автоматически группирует любые пробелы)
    words = target_text.split()
    word_count = len(words)
    
    # Выводим расширенную статистику пользователю
    await message.answer(
        f"📊 <b>Результаты анализа текста:</b>\n\n"
        f"🔹 <b>Всего слов:</b> <code>{word_count}</code>\n"
        f"🔹 <b>Символов (с пробелами):</b> <code>{total_chars}</code>\n"
        f"🔹 <b>Символов (без пробелов):</b> <code>{chars_no_spaces}</code>",
        parse_mode="HTML"
    )
    
    await state.clear()


# ПОФИКСИЛИ ЗАВИСАНИЕ СТЕЙТА: Хэндлер-перехватчик нетекстовых сообщений
@router.message(Level3States.waiting_for_text_to_analyze)
async def process_analyzer_invalid(message: Message, state: FSMContext):
    # Если юзер отправил голый стикер, документ или аудио без какого-либо текста
    await message.answer(
        "❌ Я не смог обнаружить текст в вашем сообщении!\n"
        "Пожалуйста, отправьте текстовое сообщение, подпись к медиа или напишите <b>отмена</b>."
    )