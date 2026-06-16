import io
import os
from aiogram import Router, F, html
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from utils.states import Level3States
from PIL import Image, ImageDraw, ImageFont

router = Router()

# Относительный путь к шрифту внутри проекта для независимости от операционной системы
# Перед запуском создай папку data/fonts/ и положи туда, например, arial.ttf или impact.ttf
FONT_PATH = os.path.join("data", "fonts", "arial.ttf")


# Вспомогательная функция для рисования текста с контрастной обводкой
def draw_text_with_outline(draw, text, position, font, text_color, outline_color, outline_width):
    x, y = position
    # Генерируем плотный контур за счет смещения по пиксельной сетке вокруг позиции текста
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    # Поверх контура накладываем основной текст
    draw.text(position, text, font=font, fill=text_color)


# Хэндлер инициализации генератора мемов
@router.callback_query(F.data == "cmd_meme_gen")
async def start_meme_gen(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🖼 <b>Генератор мемов 'In-Memory'</b>\n\n"
        "Шаг 1: Пришлите мне фотографию или изображение, которое вы хотите использовать как шаблон.\n\n"
        "Для отмены операции в любой момент напишите <b>отмена</b>.",
        parse_mode="HTML"
    )
    await state.set_state(Level3States.waiting_for_meme_photo)
    await callback.answer()


# Хэндлер приема изображения и сохранения его в байтовый буфер FSM
@router.message(Level3States.waiting_for_meme_photo, F.photo)
async def process_meme_photo(message: Message, state: FSMContext):
    # Берем самый качественный вариант картинки из массива
    photo = message.photo[-1]
    
    # Скачиваем изображение напрямую в байтовый поток (без сохранения на жесткий диск)
    photo_bytes = await message.bot.download(photo, destination=io.BytesIO())
    
    # Сериализуем буфер в чистые байты для хранения в контексте FSM состояния
    await state.update_data(meme_photo_bytes=photo_bytes.getvalue())
    
    await message.answer(
        "⏳ Фото получено!\n\n"
        "Шаг 2: Введите текст для мема.\n"
        "Используйте символ <code>/</code>, чтобы разделить фразу на верхний и нижний текст.\n"
        "<i>Пример: Мой код работает / Я не знаю почему</i>",
        parse_mode="HTML"
    )
    await state.set_state(Level3States.waiting_for_meme_text)


# Хэндлер перехвата текстовой отмены на этапе ожидания фото
@router.message(Level3States.waiting_for_meme_photo)
async def cancel_meme_photo(message: Message, state: FSMContext):
    if message.text and message.text.strip().lower() in ["отмена", "/cancel"]:
        await state.clear()
        await message.answer("❌ Создание мема отменено.")
        return
    await message.answer("❌ Пожалуйста, отправьте именно фотографию или напишите <b>отмена</b>.", parse_mode="HTML")


# Хэндлер обработки текста, рендеринга надписей через Pillow и отправки готового файла
@router.message(Level3States.waiting_for_meme_text, F.text)
async def process_meme_text(message: Message, state: FSMContext):
    text = message.text.strip()
    
    # Обработка ручной отмены (и очистка тяжелых байт из ОЗУ)
    if text.lower() in ["отмена", "/cancel"]:
        await state.clear()
        await message.answer("❌ Создание мема отменено.")
        return
        
    # Защита от переполнения картинки слишком длинной строкой
    if len(text) > 80:
        await message.answer("❌ Текст слишком длинный! Пожалуйста, сократите фразу до 80 символов.")
        return
    
    # Разделяем строку на верхний и нижний блоки мема
    if '/' in text:
        parts = text.split('/', 1)
        top_text = parts[0].strip().upper()
        bottom_text = parts[1].strip().upper()
    else:
        top_text = text.upper()
        bottom_text = ""
        
    # Показываем пользователю статус отправки медиафайла
    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
    
    # Извлекаем сырые байты шаблона из контекста FSM
    user_data = await state.get_data()
    photo_bytes_raw = user_data.get("meme_photo_bytes")
    
    if not photo_bytes_raw:
        await message.answer("❌ Ошибка сессии: фото не найдено в памяти. Начните процесс сначала.")
        await state.clear()
        return
        
    try:
        # Инициализируем объект Pillow Image из байтового потока
        image = Image.open(io.BytesIO(photo_bytes_raw))
        image = image.convert("RGB")
        
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        # Динамически вычисляем оптимальный размер шрифта от высоты картинки
        font_size = int(height / 12) if height > 300 else 24
        
        # Безопасно загружаем фиксированный TTF-шрифт с поддержкой кириллицы
        if os.path.exists(FONT_PATH):
            font = ImageFont.truetype(FONT_PATH, size=font_size)
        else:
            # Откат на системный поиск, если разработчик забыл положить файл в папку
            try:
                font = ImageFont.truetype("arial.ttf", size=font_size)
            except Exception:
                font = ImageFont.load_default()
        
        margin = 15
        
        # Рендеринг верхнего текстового блока
        if top_text:
            bbox = draw.textbbox((0, 0), top_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            draw_text_with_outline(
                draw, top_text, 
                ((width - text_width) / 2, margin), 
                font, "white", "black", max(1, int(text_height / 15))
            )
            
        # Рендеринг нижнего текстового блока
        if bottom_text:
            bbox = draw.textbbox((0, 0), bottom_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            draw_text_with_outline(
                draw, bottom_text, 
                ((width - text_width) / 2, height - text_height - margin - int(font_size / 2)), 
                font, "white", "black", max(1, int(text_height / 15))
            )
            
        # Сохраняем готовую картинку обратно в оперативную память
        output_io = io.BytesIO()
        image.save(output_io, format="JPEG", quality=90)
        output_io.seek(0)
        
        # Отправляем сгенерированное медиа пользователю напрямую из буфера ОЗУ
        await message.answer_photo(
            BufferedInputFile(output_io.read(), filename="meme.jpg"), 
            caption="🎉 <b>Ваш мем готов!</b>",
            parse_mode="HTML"
        )
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Не удалось сгенерировать мем. Ошибка: {e}")
        await state.clear()