import io
import qrcode
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from utils.states import Level2States

router = Router()

# 1. Ловим клик по кнопке из level2_menu
@router.callback_query(F.data == "cmd_qrcode_gen")
async def start_qrcode(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🔲 <b>QR-код генератор</b>\n\n"
        "Отправьте мне любой текст или ссылку, и я превращу её в QR-код:",
        parse_mode="HTML"
    )
    # Включаем микро-состояние ожидания текста
    await state.set_state(Level2States.waiting_for_qr_text)
    await callback.answer()


# 2. Ловим текст, когда пользователь находится в нужном состоянии
@router.message(Level2States.waiting_for_qr_text)
async def process_qrcode(message: Message, state: FSMContext):
    text_to_encode = message.text.strip()
    
    # Отправляем фейковое действие "отправка фото", чтобы юзер видел, что бот думает
    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
    
    try:
        # Настраиваем генератор QR-кода
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(text_to_encode)
        qr.make(fit=True)

        # Рендерим QR-код в PIL-картинку
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Ссылаем картинку в байты (в оперативку), чтобы не создавать мусорные файлы на сервере
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0) # Перемещаем указатель в начало байтового потока
        
        # Упаковываем байты для отправки в aiogram 3.x
        photo_file = BufferedInputFile(buffer.read(), filename="qrcode.png")
        
        await message.answer_photo(
            photo=photo_file,
            caption=f"✅ <b>Ваш QR-код готов!</b>\n\nЗакодированный текст:\n<code>{text_to_encode}</code>",
            parse_mode="HTML"
        )
        
        # Сбрасываем микро-состояние
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при генерации QR-кода: {e}")
        await state.clear()