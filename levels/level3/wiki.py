import wikipediaapi
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level3States

router = Router()

# Инициализируем API (указываем user-agent, как того требует Википедия)
wiki_wiki = wikipediaapi.Wikipedia(
    language='ru',
    user_agent='super-telegram-bot (contact: myemail@example.com)'
)

@router.callback_query(F.data == "cmd_wiki")
async def start_wiki(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📖 Введите тему, которую хотите найти в Википедии:")
    await state.set_state(Level3States.waiting_for_wiki_query)
    await callback.answer()

@router.message(Level3States.waiting_for_wiki_query)
async def process_wiki_search(message: Message, state: FSMContext):
    query = message.text
    page = wiki_wiki.page(query)
    
    if page.exists():
        summary = page.summary[:500] + "..." if len(page.summary) > 500 else page.summary
        response_text = (
            f"🔎 <b>{page.title}</b>\n\n"
            f"{summary}\n\n"
            f"🔗 <a href='{page.fullurl}'>Читать полностью</a>"
        )
        await message.answer(response_text, parse_mode="HTML")
    else:
        await message.answer("❌ Статья не найдена. Попробуйте другой запрос.")
        
    await state.clear()