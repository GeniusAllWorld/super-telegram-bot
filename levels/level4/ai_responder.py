import os
import aiohttp
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from utils.states import Level4States
from config import AI_API_KEY

router = Router()

# Официальный API эндпоинт GroqCloud
API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Быстрая и точная модель Llama 3 на Groq
MODEL_NAME = "llama-3.1-8b-instant"

def get_cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Выйти из ИИ")]],
        resize_keyboard=True
    )

@router.callback_query(F.data == "cmd_ai_respond")
async def start_ai_mode(callback: CallbackQuery, state: FSMContext):
    if not AI_API_KEY:
        await callback.message.answer("❌ В .env не задан AI_API_KEY (нужен ключ gsk_...)")
        await callback.answer()
        return

    await callback.message.answer(
        "🧠 <b>Режим ИИ-Автоответчика Groq активирован!</b>\n\n"
        "Я подключен к сверхбыстрому облаку GroqCloud (Llama 3).\n"
        "Напиши мне что-нибудь, генерация займет меньше секунды!",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await state.set_state(Level4States.ai_chat)
    await callback.answer()

@router.message(Level4States.ai_chat, F.text == "❌ Выйти из ИИ")
async def exit_ai_mode(message: Message, state: FSMContext):
    await message.answer("👋 Режим ИИ выключен. Возвращаюсь к обычным командам.", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@router.message(Level4States.ai_chat, F.text)
async def process_ai_request(message: Message):
    # Включаем статус "печатает"
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # Структура JSON запроса для Groq совпадает со стандартом OpenAI
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system", 
                "content": "Ты — умный, дружелюбный и грамотный ИИ-ассистент в Телеграм-боте. "
                           "Отвечай строго на красивом, правильном русском языке, без грамматических ошибок."
            },
            {"role": "user", "content": message.text}
        ],
        "temperature": 0.6  # Чуть снизим креативность, чтобы уменьшить число ошибок
    }
    
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, headers=headers, timeout=20) as response:
                if response.status == 200:
                    result = await response.json()
                    ai_text = result["choices"][0]["message"]["content"]
                    await message.answer(ai_text)
                else:
                    error_json = await response.json()
                    error_msg = error_json.get("error", {}).get("message", "Неизвестная ошибка API")
                    await message.answer(f"❌ Ошибка Groq API: <code>{error_msg}</code>", parse_mode="HTML")
                    
    except Exception as e:
        await message.answer(f"❌ Не удалось получить ответ от облака Groq: {e}")