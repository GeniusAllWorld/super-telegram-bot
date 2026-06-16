import os
import aiohttp
import html # Импортируем html для безопасного экранирования распознанного текста
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from utils.states import Level4States
from config import AI_API_KEY

router = Router()

# Официальный эндпоинт Groq API для транскрипции аудио
GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

# Используем топовую открытую модель Whisper от OpenAI на мощностях Groq
MODEL_NAME = "whisper-large-v3"


# Функция генерации клавиатуры отмены
def get_cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )


# 1. Срабатывает по нажатию кнопки из инлайн-меню Уровня 4
@router.callback_query(F.data == "cmd_whisper_stt")
async def start_whisper_stt(callback: CallbackQuery, state: FSMContext):
    if not AI_API_KEY:
        await callback.message.answer("❌ В .env не задан AI_API_KEY для интеграции с Groq!")
        await callback.answer()
        return

    await callback.message.answer(
        "🎙 <b>Режим распознавания речи (Whisper STT)</b>\n\n"
        "Запишите голосовое сообщение или перешлите мне любой аудиофайл, и я переведу его в текст.",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await state.set_state(Level4States.waiting_for_voice)
    await callback.answer()


# 2. Обработка кнопки отмены
@router.message(Level4States.waiting_for_voice, F.text == "❌ Отмена")
async def cancel_whisper_stt(message: Message, state: FSMContext):
    await message.answer("📥 Режим распознавания речи отменен.", reply_markup=ReplyKeyboardRemove())
    await state.clear()


# 3. Ловим голосовые сообщения и аудиофайлы, когда бот находится в нужном стейте
@router.message(Level4States.waiting_for_voice, F.voice | F.audio)
async def process_voice_message(message: Message, state: FSMContext):
    # Показываем статус набора текста пользователю
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # ПОФИКСИЛИ ПРИЕМ АУДИО: Универсально извлекаем file_id (для voice или для обычного audio)
    audio_obj = message.voice if message.voice else message.audio
    file_info = await message.bot.get_file(audio_obj.file_id)
    
    # Формируем имя и расширение файла для корректной обработки на стороне API
    filename = "voice.ogg" if message.voice else getattr(message.audio, "file_name", "audio.mp3")
    content_type = "audio/ogg" if message.voice else getattr(message.audio, "mime_type", "audio/mpeg")
    
    file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file_info.file_path}"
    
    try:
        async with aiohttp.ClientSession() as session:
            # 1. Загружаем аудиофайл с серверов Телеграма в оперативную память бота
            async with session.get(file_url, timeout=15) as tg_resp:
                if tg_resp.status != 200:
                    await message.reply("❌ Не удалось скачать аудиофайл из Telegram.", reply_markup=ReplyKeyboardRemove())
                    await state.clear()
                    return
                audio_bytes = await tg_resp.read()
            
            # 2. Формируем Multipart FormData
            data = aiohttp.FormData()
            data.add_field('model', MODEL_NAME)
            data.add_field('file', audio_bytes, filename=filename, content_type=content_type)
            data.add_field('language', 'ru')
            
            headers = {"Authorization": f"Bearer {AI_API_KEY}"}
            
            # 3. Отправляем запрос на сервера Groq
            async with session.post(GROQ_AUDIO_URL, data=data, headers=headers, timeout=30) as groq_resp:
                if groq_resp.status == 200:
                    result = await groq_resp.json()
                    raw_text = result.get("text", "").strip()
                    
                    if raw_text:
                        # ПОФИКСИЛИ HTML-ИНЪЕКЦИЮ: Обязательно экранируем распознанный текст
                        # Теперь бот никогда не упадет из-за спецсимволов в расшифровке речи
                        safe_text = html.escape(raw_text)
                        await message.reply(
                            f"🗣 <b>Распознанный текст:</b>\n\n«{safe_text}»", 
                            reply_markup=ReplyKeyboardRemove(), 
                            parse_mode="HTML"
                        )
                    else:
                        await message.reply("🤷‍♂️ Аудио успешно обработано, но членораздельной речи не обнаружено.", reply_markup=ReplyKeyboardRemove())
                else:
                    await message.answer(f"❌ Ошибка Whisper API. Статус-код: {groq_resp.status}", reply_markup=ReplyKeyboardRemove())
                    
    except Exception as e:
        await message.answer(f"❌ Произошла непредвиденная ошибка: {html.escape(str(e))}", reply_markup=ReplyKeyboardRemove())
        
    await state.clear()


# 4. Если юзер в режиме ожидания аудио прислал обычный текст/мусор
@router.message(Level4States.waiting_for_voice)
async def voice_stt_invalid_format(message: Message):
    # Не удаляем клавиатуру отмены (get_cancel_kb), чтобы пользователь не застрял в стейте навсегда
    await message.answer(
        "⚠️ Пожалуйста, пришлите именно <b>голосовое сообщение</b> или <b>аудиофайл</b>, либо нажмите «❌ Отмена»", 
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )