import os
import aiohttp
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from utils.states import Level4States
from config import AI_API_KEY

router = Router()

GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

MODEL_NAME = "whisper-large-v3"

def get_cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

# 1. Срабатывает по нажатию кнопки из инлайн-меню Уровня 4
@router.callback_query(F.data == "cmd_whisper_stt")
async def start_whisper_stt(callback: CallbackQuery, state: FSMContext):
    if not AI_API_KEY:
        await callback.message.answer("❌ В .env не задан AI_API_KEY!")
        await callback.answer()
        return

    await callback.message.answer(
        "🎙 <b>Режим распознавания речи (Whisper STT)</b>\n\n"
        "Запишите или перешлите мне голосовое сообщение, и я переведу его в текст.",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    # Включаем состояние ожидания голосовухи
    await state.set_state(Level4States.waiting_for_voice)
    await callback.answer()

# 2. Обработка кнопки отмены
@router.message(Level4States.waiting_for_voice, F.text == "❌ Отмена")
async def cancel_whisper_stt(message: Message, state: FSMContext):
    await message.answer("📥 Режим распознавания отменен.", reply_markup=ReplyKeyboardRemove())
    await state.clear()

# 3. Ловим голосовуху ТОЛЬКО когда бот находится в нужном стейте
@router.message(Level4States.waiting_for_voice, F.voice)
async def process_voice_message(message: Message, state: FSMContext):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    voice = message.voice
    file_info = await message.bot.get_file(voice.file_id)
    file_path = file_info.file_path
    file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file_path}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as tg_resp:
                if tg_resp.status != 200:
                    await message.answer("❌ Не удалось скачать файл из Telegram.", reply_markup=ReplyKeyboardRemove())
                    await state.clear()
                    return
                audio_bytes = await tg_resp.read()
            
            data = aiohttp.FormData()
            data.add_field('model', MODEL_NAME)
            data.add_field('file', audio_bytes, filename='voice.ogg', content_type='audio/ogg')
            data.add_field('language', 'ru')
            
            headers = {"Authorization": f"Bearer {AI_API_KEY}"}
            
            async with session.post(GROQ_AUDIO_URL, data=data, headers=headers, timeout=30) as groq_resp:
                if groq_resp.status == 200:
                    result = await groq_resp.json()
                    text_result = result.get("text", "").strip()
                    
                    if text_result:
                        await message.reply(
                            f"🗣 <b>Распознанный текст:</b>\n\n«{text_result}»", 
                            reply_markup=ReplyKeyboardRemove(), 
                            parse_mode="HTML"
                        )
                    else:
                        await message.reply("🤷‍♂️ Аудио обработано, но слов не найдено.", reply_markup=ReplyKeyboardRemove())
                else:
                    error_text = await groq_resp.text()
                    await message.answer(f"❌ Ошибка Whisper API: {groq_resp.status}", reply_markup=ReplyKeyboardRemove())
                    
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=ReplyKeyboardRemove())
        
    # Сбрасываем состояние после успешной обработки или падения
    await state.clear()

# 4. Если юзер в режиме ожидания аудио прислал обычный текст вместо голосовухи
@router.message(Level4States.waiting_for_voice)
async def voice_stt_invalid_format(message: Message):
    await message.answer("⚠️ Пожалуйста, пришлите именно <b>голосовое сообщение</b> или нажмите кнопку «❌ Отмена»", parse_mode="HTML")