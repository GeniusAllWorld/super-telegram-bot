import os
import aiohttp
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from utils.states import Level4States
from config import OCR_API_KEY

router = Router()

OCR_URL = "https://api.ocr.space/parse/image"

def get_cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

# 1. Срабатывает при нажатии кнопки "Текст с фото (OCR)"
@router.callback_query(F.data == "cmd_tesseract_ocr")
async def start_ocr_mode(callback: CallbackQuery, state: FSMContext):
    if not OCR_API_KEY:
        await callback.message.answer("❌ В .env не задан OCR_API_KEY!")
        await callback.answer()
        return

    await callback.message.answer(
        "👁 <b>Режим распознавания текста с фото (OCR)</b>\n\n"
        "Пришлите мне картинку или скриншот, на котором есть текст (на русском или английском), и я его вытащу.",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await state.set_state(Level4States.waiting_for_photo)
    await callback.answer()

# 2. Сброс состояния при отмене
@router.message(Level4States.waiting_for_photo, F.text == "❌ Отмена")
async def cancel_ocr(message: Message, state: FSMContext):
    await message.answer("📥 Режим OCR отменен.", reply_markup=ReplyKeyboardRemove())
    await state.clear()

# 3. Ловим ФОТО, когда бот в нужном стейте
@router.message(Level4States.waiting_for_photo, F.photo)
async def process_ocr_photo(message: Message, state: FSMContext):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # Берем лучшее качество
    photo = message.photo[-1]
    file_info = await message.bot.get_file(photo.file_id)
    file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file_info.file_path}"
    
    try:
        async with aiohttp.ClientSession() as session:
            # 1. Скачиваем фото в память бота
            async with session.get(file_url) as tg_resp:
                if tg_resp.status != 200:
                    await message.answer("❌ Не удалось скачать фото из Telegram.", reply_markup=ReplyKeyboardRemove())
                    await state.clear()
                    return
                photo_bytes = await tg_resp.read()
            
            # 2. Формируем FormData и передаем файл КАРТИНКОЙ, а не ссылкой
            data = aiohttp.FormData()
            data.add_field('apikey', OCR_API_KEY)
            data.add_field('language', 'rus')
            # Передаем байты, жестко указав имя файла с расширением
            data.add_field('file', photo_bytes, filename='image.png', content_type='image/png')
            
            # 3. Пуляем в API
            async with session.post(OCR_URL, data=data, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    parsed_results = result.get("ParsedResults", [])
                    
                    if parsed_results:
                        extracted_text = parsed_results[0].get("ParsedText", "").strip()
                        
                        if extracted_text:
                            await message.reply(
                                f"📝 <b>Распознанный текст:</b>\n\n<code>{extracted_text}</code>", 
                                reply_markup=ReplyKeyboardRemove(),
                                parse_mode="HTML"
                            )
                        else:
                            await message.reply("🤷‍♂️ Текст на картинке не обнаружен (возможно, шрифт слишком специфичный).", reply_markup=ReplyKeyboardRemove())
                    else:
                        error_msg = result.get("ErrorMessage", ["Неизвестная ошибка API"])[0]
                        await message.reply(f"❌ Ошибка OCR: {error_msg}", reply_markup=ReplyKeyboardRemove())
                else:
                    await message.answer(f"❌ Ошибка сервера API. Статус: {response.status}", reply_markup=ReplyKeyboardRemove())
                    
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {e}", reply_markup=ReplyKeyboardRemove())
        
    await state.clear()

# 4. Если вместо фото прислали бред
@router.message(Level4States.waiting_for_photo)
async def ocr_invalid_format(message: Message):
    await message.answer("⚠️ Пожалуйста, пришлите именно <b>фотографию</b> или нажмите «❌ Отмена»", parse_mode="HTML")