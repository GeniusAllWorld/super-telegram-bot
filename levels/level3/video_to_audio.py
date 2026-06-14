import os
import subprocess
import io
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from utils.states import Level3States

from config import FFMPEG_PATH

router = Router()

@router.callback_query(F.data == "cmd_video_to_audio")
async def start_converter(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🎞 Пришлите мне короткое видео (до 20МБ), а я извлеку из него аудиодорожку.")
    await state.set_state(Level3States.waiting_for_video)
    await callback.answer()

@router.message(Level3States.waiting_for_video, F.video)
async def process_video(message: Message, state: FSMContext):
    await message.answer("🔄 Конвертирую... Подождите пару секунд.")
    
    # 1. Создаем уникальные имена файлов для процесса
    input_filename = f"temp_{message.from_user.id}.mp4"
    output_filename = f"temp_{message.from_user.id}.mp3"
    
    try:
        # 2. Скачиваем видео на диск (ffmpeg требует файл)
        await message.bot.download(message.video, destination=input_filename)
        
        # 3. Запускаем ffmpeg через subprocess
        # -i: входной файл, -vn: отключить видео, -acodec libmp3lame: кодек mp3
        cmd = [FFMPEG_PATH, "-i", input_filename, "-vn", "-acodec", "libmp3lame", "-q:a", "2", output_filename, "-y"]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 4. Читаем готовый файл в память
        with open(output_filename, "rb") as audio_file:
            audio_data = audio_file.read()
            
        # 5. Отправляем пользователю
        await message.answer_audio(
            BufferedInputFile(audio_data, filename="audio.mp3"),
            caption="🎧 Ваша аудиодорожка готова!"
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка конвертации: {str(e)}")
        
    finally:
        # 6. ЧИСТКА (Критически важно!)
        if os.path.exists(input_filename):
            os.remove(input_filename)
        if os.path.exists(output_filename):
            os.remove(output_filename)
            
    await state.clear()