import os
import aiohttp
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from utils.states import Level4States
from config import AI_API_KEY

router = Router()

# Официальный API эндпоинт GroqCloud
API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Быстрая и точная модель Llama 3 на Groq
MODEL_NAME = "llama-3.1-8b-instant"


# Клавиатура выхода из ИИ режима
def get_cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Выйти из ИИ")]],
        resize_keyboard=True
    )


# Хэндлер активации режима чата с ИИ
@router.callback_query(F.data == "cmd_ai_respond")
async def start_ai_mode(callback: CallbackQuery, state: FSMContext):
    if not AI_API_KEY:
        await callback.message.answer("❌ В .env не задан AI_API_KEY (нужен ключ gsk_...)")
        await callback.answer()
        return

    await callback.message.answer(
        "🧠 <b>Режим ИИ-Автоответчика Groq активирован!</b>\n\n"
        "Я подключен к сверхбыстрому облаку GroqCloud (Llama 3).\n"
        "Напиши мне любой вопрос, и я отвечу на него.\n"
        "Чтобы вернуться в меню, нажми кнопку ниже:",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await state.set_state(Level4States.ai_chat)
    await callback.answer()


# Хэндлер выхода из режима ИИ и очистки FSM памяти
@router.message(Level4States.ai_chat, F.text == "❌ Выйти из ИИ")
async def exit_ai_mode(message: Message, state: FSMContext):
    await message.answer("👋 Режим ИИ выключен. Возвращаюсь к обычным командам.", reply_markup=ReplyKeyboardRemove())
    await state.clear()


# Основной хэндлер отправки запроса в Groq API и обработки ответа
@router.message(Level4States.ai_chat, F.text)
async def process_ai_request(message: Message):
    # Постоянно отправляем экшен «печатает», имитируя генерацию мысли ИИ
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # Конфигурируем системный промпт, запрещая ИИ использовать сложную разметку таблиц
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system", 
                "content": "Ты — умный, дружелюбный и грамотный ИИ-ассистент в Телеграм-боте. "
                           "Отвечай строго на красивом, правильном русском языке. "
                           "Используй стандартный Markdown для выделения важных мыслей, если необходимо."
            },
            {"role": "user", "content": message.text}
        ],
        "temperature": 0.6
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
                    
                    try:
                        # ПОФИКСИЛИ МАРКДАУН-КРАШ: Пытаемся отправить ответ в Markdown, как генерирует Llama 3
                        await message.answer(ai_text, parse_mode="Markdown")
                    except TelegramBadRequest:
                        # Если нейросеть сгенерировала битые теги разметки, отправляем ее как обычный текст
                        await message.answer(ai_text)
                else:
                    # Корректно обрабатываем ошибки лимитов или баланса ключа Groq
                    error_json = await response.json()
                    error_msg = error_json.get("error", {}).get("message", "Неизвестная ошибка API")
                    await message.answer(f"❌ Ошибка Groq API: <code>{error_msg}</code>", parse_mode="HTML")
                    
    except Exception as e:
        await message.answer(f"❌ Не удалось получить ответ от облака Groq. Проверьте соединение. Ошибка: {e}")


# ПОФИКСИЛИ ЗАВИСАНИЕ ИНТЕРФЕЙСА: Перехватываем картинки, стикеры и файлы, отправленные вместо текста
@router.message(Level4States.ai_chat)
async def process_ai_request_invalid(message: Message):
    await message.answer(
        "⚠️ Текущая модель Llama 3 умеет обрабатывать только текстовые сообщения!\n"
        "Пожалуйста, введите ваш вопрос текстом или нажмите кнопку <b>❌ Выйти из ИИ</b>.",
        parse_mode="HTML"
    )