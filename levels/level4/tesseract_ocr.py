import os
import aiohttp
import html # Импортируем html для защиты вывода от инъекций разметки
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from utils.states import Level4States
from config import OCR_API_KEY

router = Router()

# Официальный эндпоинт бесплатного/профессионального API OCR.Space
OCR_URL = "https://api.ocr.space/parse/image"


# Клавиатура отмены режима ожидания изображения
def get_cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )


# 1. Срабатывает при нажатии кнопки "Текст с фото (OCR)"
@router.callback_query(F.data == "cmd_tesseract_ocr")
async def start_ocr_mode(callback: CallbackQuery, state: FSMContext):
    if not OCR_API_KEY:
        await callback.message.answer("❌ В .env не задан OCR_API_KEY (необходим ключ от ocr.space)!")
        await callback.answer()
        return

    await callback.message.answer(
        "👁 <b>Режим распознавания текста с фото (OCR)</b>\n\n"
        "Пришлите мне картинку, скриншот или документ-изображение, на котором есть текст (на русском или английском), и я его вытащу.",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await state.set_state(Level4States.waiting_for_photo)
    await callback.answer()


# 2. Сброс состояния при ручной отмене
@router.message(Level4States.waiting_for_photo, F.text == "❌ Отмена")
async def cancel_ocr(message: Message, state: FSMContext):
    await message.answer("📥 Режим OCR отменен.", reply_markup=ReplyKeyboardRemove())
    await state.clear()


# 3. Ловим ФОТО (или изображение без сжатия в виде документа), когда бот в нужном стейте
@router.message(Level4States.waiting_for_photo, F.photo | F.document.mime_type.startswith("image/"))
async def process_ocr_photo(message: Message, state: FSMContext):
    # Включаем статус печати бота, показывая пользователю активность
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # ПОФИКСИЛИ ПРИЕМ ДОКУМЕНТОВ: Динамически извлекаем file_id в зависимости от того, как отправлен файл
    if message.photo:
        # Берем самый большой и качественный вариант фотографии из массива
        file_id = message.photo[-1].file_id
    else:
        file_id = message.document.file_id
        
    try:
        file_info = await message.bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file_info.file_path}"
        
        async with aiohttp.ClientSession() as session:
            # 1. Скачиваем фото во временную оперативную память (Bytes)
            async with session.get(file_url, timeout=15) as tg_resp:
                if tg_resp.status != 200:
                    await message.reply("❌ Не удалось загрузить файл с серверов Telegram. Попробуйте позже.", reply_markup=ReplyKeyboardRemove())
                    await state.clear()
                    return
                photo_bytes = await tg_resp.read()
            
            # 2. Формируем Multipart FormData для отправки бинарных данных в API
            data = aiohttp.FormData()
            data.add_field('apikey', OCR_API_KEY)
            # engine=2 лучше и быстрее распознает кириллицу и мелкие символы
            data.add_field('OCREngine', '2') 
            data.add_field('language', 'rus')
            data.add_field('file', photo_bytes, filename='image.png', content_type='image/png')
            
            # 3. Отправляем запрос на сервер распознавания с таймаутом ожидания
            async with session.post(OCR_URL, data=data, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    parsed_results = result.get("ParsedResults", [])
                    
                    if parsed_results:
                        raw_text = parsed_results[0].get("ParsedText", "").strip()
                        
                        if raw_text:
                            # ПОФИКСИЛИ HTML-ИНЪЕКЦИЮ: Строго экранируем распознанный текст.
                            # Если на фото были знаки < или >, бот больше не упадет с ошибкой разметки.
                            extracted_text = html.escape(raw_text)
                            await message.reply(
                                f"📝 <b>Распознанный текст:</b>\n\n<code>{extracted_text}</code>", 
                                reply_markup=ReplyKeyboardRemove(),
                                parse_mode="HTML"
                            )
                        else:
                            await message.reply("🤷‍♂️ Текст на картинке не обнаружен. Попробуйте сделать снимок более четким.", reply_markup=ReplyKeyboardRemove())
                    else:
                        # ПОФИКСИЛИ ОШИБКУ ИНДЕКСАЦИИ СТРОКИ: Безопасно парсим ошибку, если она вернулась строкой
                        raw_error = result.get("ErrorMessage", "Неизвестная ошибка API")
                        error_msg = raw_error if isinstance(raw_error, str) else str(raw_error)
                        await message.reply(f"❌ Ошибка OCR сервиса: {html.escape(error_msg)}", reply_markup=ReplyKeyboardRemove())
                else:
                    await message.answer(f"❌ Ошибка внешнего сервера API. Статус-код: {response.status}", reply_markup=ReplyKeyboardRemove())
                    
    except Exception as e:
        await message.answer(f"❌ Не удалось обработать изображение. Ошибка: {html.escape(str(e))}", reply_markup=ReplyKeyboardRemove())
        
    await state.clear()


# 4. Если вместо фото или картинки-документа прислали текст/мусор
@router.message(Level4States.waiting_for_photo)
async def ocr_invalid_format(message: Message):
    await message.answer("⚠️ Пожалуйста, пришлите именно <b>фотографию</b> (или картинку файлом), либо нажмите «❌ Отмена»", parse_mode="HTML")