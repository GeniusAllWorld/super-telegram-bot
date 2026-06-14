import aiohttp
import os
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level3States # Не забудь добавить state в utils/states.py
from config import GIPHY_API_KEY

router = Router()

@router.callback_query(F.data == "cmd_gif_search")
async def start_gif_search(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🎞 Введите ключевое слово для поиска GIF (например, 'cat' или 'dance'):")
    await state.set_state(Level3States.waiting_for_gif_query)
    await callback.answer()

@router.message(Level3States.waiting_for_gif_query)
async def process_gif_search(message: Message, state: FSMContext):
    query = message.text
    
    # URL для поиска GIF через Giphy
    url = f"https://api.giphy.com/v1/gifs/search?api_key={GIPHY_API_KEY}&q={query}&limit=1&rating=g"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data['data']:
                    # Получаем прямую ссылку на GIF
                    gif_url = data['data'][0]['images']['original']['url']
                    await message.answer_animation(animation=gif_url)
                else:
                    await message.answer("❌ Ничего не нашел по этому запросу.")
            else:
                await message.answer("❌ Ошибка при обращении к API Giphy.")
    
    await state.clear()