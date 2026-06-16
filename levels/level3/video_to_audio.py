import asyncio
import os
import time
from aiogram import Router, F, html
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from utils.states import Level3States

# Импортируем путь к исполняемому файлу FFmpeg из конфига
from config import FFMPEG_PATH

router = Router()


# Хэндлер инициализации конвертера видео в аудио
@router.callback_query(F.data == "cmd_video_to_audio")
async def start_converter(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🎞 <b>Экстрактор аудиодорожек (MP3)</b>\n\n"
        "Пришлите мне короткое видео (до 20МБ), а я извлеку из него аудиодорожку.\n"
        "Для отмены операции напишите <b>отмена</b>.",
        parse_mode="HTML"
    )
    await state.set_state(Level3States.waiting_for_video)
    await callback.answer()


# Хэндлер приема видеофайла, асинхронной конвертации через FFmpeg и отправки результата
@router.message(Level3States.waiting_for_video, F.video)
async def process_video(message: Message, state: FSMContext):
    # Убираем дублирование: сбрасываем стейт сразу после получения валидного видео
    await state.clear()
    
    # Жесткое ограничение на размер входящего видео (20 * 1024 * 1024 байт)
    if message.video.file_size > 20971520:
        await message.answer("❌ Файл слишком тяжелый! Пожалуйста, отправьте видео размером до 20МБ.")
        return

    status_msg = await message.answer("⏳ Скачиваю видео... Подождите пару секунд.")
    
    # 1. Пофиксили конфликт файлов: создаем гарантированно уникальные имена через timestamp
    unique_id = f"{message.from_user.id}_{int(time.time())}"
    input_filename = f"temp_in_{unique_id}.mp4"
    output_filename = f"temp_out_{unique_id}.mp3"
    
    try:
        # Включаем экшен загрузки аудио в интерфейсе
        await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_voice")
        
        # 2. Скачиваем видео на жесткий диск (для работы FFmpeg)
        await message.bot.download(message.video, destination=input_filename)
        
        await status_msg.edit_text("🔄 Конвертирую видео в MP3... (Асинхронно)")
        
        # 3. ПОФИКСИЛИ БЛОКИРОВКУ: запускаем FFmpeg через АСИНХРОННЫЙ subprocess
        cmd = [
            FFMPEG_PATH, "-i", input_filename, 
            "-vn", "-acodec", "libmp3lame", "-q:a", "2", 
            output_filename, "-y"
        ]
        
        # Создаем процесс, но не блокируем Event Loop бота
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        
        # Асинхронно ждем завершения конвертации, пока бот обрабатывает других юзеров
        await process.wait()
        
        if not os.path.exists(output_filename):
            raise FileNotFoundError("FFmpeg не сгенерировал выходной файл.")
            
        # 4. Читаем готовый аудиофайл в оперативную память (для BufferedInputFile)
        # Так как ffmpeg закрыл файл, мы можем безопасно открыть его синхронно (rb)
        with open(output_filename, "rb") as audio_file:
            audio_data = audio_file.read()
            
        # 5. Отправляем пользователю BufferedInputFile напрямую из ОЗУ
        await status_msg.delete() # Удаляем статус загрузки
        await message.answer_audio(
            BufferedInputFile(audio_data, filename="audio.mp3"),
            caption="🎧 Ваша аудиодорожка готова!\n\n(Извлечено из пересланного видео)"
        )
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка конвертации или FFmpeg: {str(e)}")
        
    finally:
        # 6. ЧИСТКА (Критически важно для места на сервере)
        # try/except защищает от ошибки удаления, если файл не успел создаться
        try:
            if os.path.exists(input_filename):
                os.remove(input_filename)
            if os.path.exists(output_filename):
                os.remove(output_filename)
        except Exception:
            pass
            

# Хэндлер перехвата невалидных типов данных или отмены
@router.message(Level3States.waiting_for_video)
async def cancel_video_invalid(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    
    # Обработка ручной отмены операции
    if text.lower() in ["отмена", "/cancel"]:
        await state.clear()
        await message.answer("❌ Конвертация видео отменена.")
        return
        
    # Если юзер прислал текст или картинку вместо видео
    await message.answer(
        "❌ Это не видео! Пожалуйста, пришлите короткое видеофайлом или напишите <b>отмена</b>.",
        parse_mode="HTML"
    )