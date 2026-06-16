import aiohttp
from urllib.parse import quote
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level3States
from config import GIPHY_API_KEY

router = Router()


# Хэндлер инициализации поиска GIF-анимаций
@router.callback_query(F.data == "cmd_gif_search")
async def start_gif_search(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🎞 <b>Поиск GIF-анимаций</b>\n\n"
        "Введите ключевое слово для поиска GIF (например, <i>cat</i> или <i>dance</i>).\n"
        "Для отмены операции напишите <b>отмена</b>.",
        parse_mode="HTML"
    )
    await state.set_state(Level3States.waiting_for_gif_query)
    await callback.answer()


# Хэндлер запроса к Giphy API, кодирования параметров и отправки анимации
@router.message(Level3States.waiting_for_gif_query)
async def process_gif_search(message: Message, state: FSMContext):
    query = message.text.strip()
    
    # Обработка ручной отмены операции
    if query.lower() in ["отмена", "/cancel"]:
        await state.clear()
        await message.answer("❌ Поиск GIF отменен.")
        return

    # Включаем анимацию отправки документа, чтобы юзер видел, что бот ищет файл
    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_document")
    
    # Пофиксили кодирование: экранируем пробелы и кириллицу для безопасного URL-запроса
    safe_query = quote(query)
    url = f"https://api.giphy.com/v1/gifs/search?api_key={GIPHY_API_KEY}&q={safe_query}&limit=1&rating=g"
    
    try:
        # Открываем асинхронную сессию для отправки HTTP-запроса
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                if response.status != 200:
                    await message.answer("❌ Ошибка при обращении к API Giphy. Попробуйте позже.")
                    await state.clear()
                    return
                
                data = await response.json()
                
                # Проверяем, вернул ли нам сервер хотя бы один GIF-объект
                if data and data.get('data'):
                    # Извлекаем прямую ссылку на оригинальный GIF файл
                    gif_url = data['data'][0]['images']['original']['url']
                    
                    # Отправляем анимацию пользователю на лету по URL
                    await message.answer_animation(animation=gif_url)
                    await state.clear()
                else:
                    await message.answer("❌ Ничего не найдено по этому запросу. Попробуйте другое слово:")
                    # Не сбрасываем стейт, давая пользователю шанс ввести другое слово
                    
    except Exception as e:
        await message.answer(f"❌ Произошла непредвиденная ошибка при поиске: {e}")
        await state.clear()