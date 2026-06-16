import aiohttp
from aiogram import Router, F, html
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level2States

router = Router()

# Базовый URL бесплатного API TinyURL (не требует токенов)
TINYURL_API = "http://tinyurl.com/api-create.php?url="


# Хэндлер инициализации сокращателя ссылок
@router.callback_query(F.data == "cmd_shortener")
async def start_shortener(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🔗 <b>Сокращатель ссылок</b>\n\n"
        "Отправьте мне длинную ссылку (обязательно с <code>http://</code> или <code>https://</code>).\n"
        "Для выхода из режима отправьте слово <b>отмена</b>.",
        parse_mode="HTML"
    )
    await state.set_state(Level2States.waiting_for_url)
    await callback.answer()


# Хэндлер отправки ссылки в API, валидации и возврата короткого URL
@router.message(Level2States.waiting_for_url)
async def process_shortener(message: Message, state: FSMContext):
    url = message.text.strip()
    
    # Обработка ручной отмены операции
    if url.lower() in ["отмена", "/cancel"]:
        await state.clear()
        await message.answer("❌ Сокращение ссылки отменено.")
        return

    # Базовая валидация структуры ссылки
    if not (url.startswith("http://") or url.startswith("https://")):
        await message.answer("❌ Ссылка должна начинаться с <code>http://</code> или <code>https://</code>. Попробуйте еще раз:")
        return

    # Включаем анимацию "typing" в интерфейсе Telegram
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        # Асинхронно стучимся в API TinyURL
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{TINYURL_API}{url}", timeout=5) as response:
                if response.status != 200:
                    await message.answer("❌ Не удалось сократить ссылку. Возможно, сервис временно недоступен.")
                    await state.clear()
                    return
                
                # Извлекаем готовый текстовый URL из ответа
                short_url = await response.text()
                
                # Безопасно экранируем оригинальный URL пользователя для предотвращения HTML-ошибок Telegram
                safe_url = html.quote(url)
                
                # Пофиксили Scope: отправляем сообщение строго внутри открытого контекста обработки
                await message.answer(
                    f"✅ <b>Ссылка успешно сокращена!</b>\n\n"
                    f"📥 Оригинал: {safe_url}\n"
                    f"🚀 Результат: <code>{short_url}</code>\n\n"
                    f"<i>💡 Нажмите на результат, чтобы скопировать.</i>",
                    parse_mode="HTML"
                )
                await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при обращении к API: {e}")
        await state.clear()