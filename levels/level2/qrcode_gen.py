import io
import qrcode
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from utils.states import Level2States

router = Router()

# Хэндлер инициации генератора QR-кодов
@router.callback_query(F.data == "cmd_qrcode_gen")
async def start_qrcode(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "𔔁 <b>QR-код генератор</b>\n\n"
        "Отправьте мне любой текст или ссылку, и я превращу её в QR-код.\n"
        "Для выхода из режима отправьте слово <b>отмена</b>.",
        parse_mode="HTML"
    )
    await state.set_state(Level2States.waiting_for_qr_text)
    await callback.answer()


# Хэндлер обработки текста, генерации графического QR-кода в памяти и отправки пользователю
@router.message(Level2States.waiting_for_qr_text)
async def process_qrcode(message: Message, state: FSMContext):
    text_to_encode = message.text.strip()
    
    # Обработка ручной отмены операции
    if text_to_encode.lower() in ["отмена", "/cancel"]:
        await state.clear()
        await message.answer("❌ Генерация QR-кода отменена.")
        return
        
    # Включаем анимацию "отправка фото" в чате для имитации бурной деятельности бота
    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
    
    try:
        # Пофиксили лимиты: ставим version=None, чтобы библиотека сама расширяла QR-код под длинные ссылки
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(text_to_encode)
        qr.make(fit=True)

        # Рендерим матрицу QR-кода в изображение
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Создаем буфер в оперативной памяти
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        
        # Пофиксили баг чтения: вытаскиваем байты через .getvalue(), это гарантирует их сохранность для aiogram
        photo_file = BufferedInputFile(buffer.getvalue(), filename="qrcode.png")
        
        # Отправляем готовое изображение пользователю
        await message.answer_photo(
            photo=photo_file,
            caption=f"✅ <b>Ваш QR-код успешно сгенерирован!</b>\n\n"
                    f"📝 Закодированный текст:\n<code>{text_to_encode}</code>",
            parse_mode="HTML"
        )
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при генерации QR-кода: {e}")
        await state.clear()