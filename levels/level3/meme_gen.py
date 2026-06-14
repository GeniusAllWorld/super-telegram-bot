import io
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from utils.states import Level3States
from PIL import Image, ImageDraw, ImageFont

router = Router()

# Помощник для рисования текста с контуром
def draw_text_with_outline(draw, text, position, font, text_color, outline_color, outline_width):
    x, y = position
    # Рисуем контур (8 раз вокруг основной позиции)
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    # Рисуем основной текст
    draw.text(position, text, font=font, fill=text_color)


@router.callback_query(F.data == "cmd_meme_gen")
async def start_meme_gen(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🖼 <b>Генератор мемов 'In-Memory'</b>\n\n"
        "Шаг 1: Пришлите мне фотографию или изображение, которое вы хотите использовать как шаблон.\n\n"
        "<i>(Ничего не сохраняется на сервер, всё обрабатывается в оперативной памяти).</i>",
        parse_mode="HTML"
    )
    await state.set_state(Level3States.waiting_for_meme_photo)
    await callback.answer()


@router.message(Level3States.waiting_for_meme_photo, F.photo)
async def process_meme_photo(message: Message, state: FSMContext):
    # Берем фото в самом высоком разрешении
    photo = message.photo[-1]
    
    # Скачиваем фото прямо в байтовый поток (в оперативку)
    photo_bytes = await message.bot.download(photo, destination=io.BytesIO())
    
    # Чтобы сохранить байты в FSM, нужно получить из BytesIO чистые байты через getValue()
    await state.update_data(meme_photo_bytes=photo_bytes.getvalue())
    
    await message.answer(
        "⏳ Фото получено!\n\n"
        "Шаг 2: Введите текст для мема.\n"
        "Для разделения на верхний и нижний текст используйте '/' (например: <code>Мой кот / Когда я ем</code>):",
        parse_mode="HTML"
    )
    await state.set_state(Level3States.waiting_for_meme_text)


@router.message(Level3States.waiting_for_meme_text, F.text)
async def process_meme_text(message: Message, state: FSMContext):
    text = message.text.strip()
    
    # Делим текст на верх и низ
    if '/' in text:
        parts = text.split('/', 1)
        top_text = parts[0].strip().upper()
        bottom_text = parts[1].strip().upper()
    else:
        top_text = text.upper()
        bottom_text = ""
        
    # Показываем плашку "печатает"
    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
    
    # Достаем байты фото из FSM
    user_data = await state.get_data()
    photo_bytes_raw = user_data.get("meme_photo_bytes")
    
    if not photo_bytes_raw:
        await message.answer("❌ Упс! Ошибка при получении фото. Начните сначала.")
        await state.clear()
        return
        
    try:
        # 1. Загружаем Image из байтов
        image = Image.open(io.BytesIO(photo_bytes_raw))
        image = image.convert("RGB") # На всякий случай конвертируем
        
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        # 2. Настраиваем шрифт. Мы возьмем шрифт из самой системы.
        # Если это Linux-сервер, это будет сложнее, но пока мы используем
        # стандартный шрифт из Pillow. Для реального сервера лучше положить 
        # файл ArialBold.ttf в data/fonts/ и загрузить его.
        
        # Попробуем загрузить шрифт Arial Bold из системы, если он есть
        try:
            # Для Windows
            font = ImageFont.truetype("arialbd.ttf", size=int(height / 12)) 
        except Exception:
            try:
                # Для Linux (примерный путь)
                font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", size=int(height / 12))
            except Exception:
                # Если вообще нет шрифтов, используем дефолтный Pillow
                font = ImageFont.load_default()
        
        # 3. Рассчитываем позиции
        margin = 10
        
        # Верхний текст
        if top_text:
            bbox = draw.textbbox((0, 0), top_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            draw_text_with_outline(
                draw, top_text, 
                ((width - text_width) / 2, margin), 
                font, "white", "black", int(text_height/20) + 1
            )
            
        # Нижний текст
        if bottom_text:
            bbox = draw.textbbox((0, 0), bottom_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            draw_text_with_outline(
                draw, bottom_text, 
                ((width - text_width) / 2, height - text_height - margin - int(height/20)), 
                font, "white", "black", int(text_height/20) + 1
            )
            
        # 4. Сохраняем результат обратно в BytesIO (в оперативку)
        output_io = io.BytesIO()
        image.save(output_io, format="PNG")
        output_io.seek(0)
        
        # 5. Отправляем пользователю как BufferedInputFile
        await message.answer_photo(
            BufferedInputFile(output_io.read(), filename="meme.png"), 
            caption="🎉 Ваш мем готов!"
        )
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Не удалось сгенерировать мем. Ошибка: {e}")
        await state.clear()