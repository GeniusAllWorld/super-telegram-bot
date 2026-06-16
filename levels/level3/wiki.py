import asyncio
from aiogram import Router, F, html # Импортируем html для защиты от тегов
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level3States
import wikipediaapi

router = Router()

# Инициализируем API (указываем user-agent, как того требует Википедия)
wiki_wiki = wikipediaapi.Wikipedia(
    language='ru',
    user_agent='super-telegram-bot (contact: myemail@example.com)'
)


# Хэндлер инициализации поиска по Википедии
@router.callback_query(F.data == "cmd_wiki")
async def start_wiki(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📖 <b>Поиск по Википедии</b>\n\n"
        "Введите тему или термин, который вы хотите найти:\n"
        "Для отмены операции напишите <b>отмена</b>.",
        parse_mode="HTML"
    )
    await state.set_state(Level3States.waiting_for_wiki_query)
    await callback.answer()


# Хэндлер асинхронного парсинга данных Википедии и экранирования HTML
@router.message(Level3States.waiting_for_wiki_query, F.text)
async def process_wiki_search(message: Message, state: FSMContext):
    query = message.text.strip()
    
    # Обработка ручной отмены операции
    if query.lower() in ["отмена", "/cancel"]:
        await state.clear()
        await message.answer("❌ Поиск по Википедии отменен.")
        return

    # Включаем экшен поиска информации
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        # Получаем объект страницы (это легкая операция, она не делает сетевой запрос)
        page = wiki_wiki.page(query)
        
        # ПОФИКСИЛИ БЛОКИРОВКУ: Выносим синхронную проверку существования страницы в отдельный поток
        page_exists = await asyncio.to_thread(page.exists)
        
        if page_exists:
            # Асинхронно стягиваем тяжелые свойства страницы с серверов Википедии
            summary_raw = await asyncio.to_thread(lambda: page.summary)
            full_url = await asyncio.to_thread(lambda: page.fullurl)
            page_title = await asyncio.to_thread(lambda: page.title)
            
            # Обрезаем строку до лимита в 500 символов
            if len(summary_raw) > 500:
                summary_raw = summary_raw[:500] + "..."
                
            # ПОФИКСИЛИ HTML-ИНЪЕКЦИЮ: Безопасно экранируем сырой текст статьи от знаков < и >
            safe_title = html.quote(page_title)
            safe_summary = html.quote(summary_raw)
            
            # Формируем безопасное и красивое сообщение
            response_text = (
                f"🔎 <b>{safe_title}</b>\n\n"
                f"{safe_summary}\n\n"
                f"🔗 <a href='{full_url}'>Читать полностью на Википедии</a>"
            )
            await message.answer(response_text, parse_mode="HTML")
            await state.clear()
        else:
            await message.answer("❌ Статья не найдена. Попробуйте ввести запрос по-другому:")
            # Не очищаем стейт, давая юзеру шанс исправить опечатку в запросе
            
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при обращении к Википедии: {e}")
        await state.clear()


# ПОФИКСИЛИ ЗАВИСАНИЕ СТЕЙТА: Хэндлер перехвата невалидных типов данных (фото/стикеры)
@router.message(Level3States.waiting_for_wiki_query)
async def process_wiki_search_invalid(message: Message, state: FSMContext):
    await message.answer(
        "❌ Пожалуйста, отправьте текстовый запрос для поиска темы "
        "или напишите <b>отмена</b>."
    )