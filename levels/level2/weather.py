import aiohttp
from aiogram import Router, F, html
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level2States
from config import WEATHER_API_KEY

router = Router()

# Словарь соответствия системных типов погоды OpenWeatherMap и красивых эмодзи
WEATHER_EMOJIS = {
    "Clear": "☀️ Ясно",
    "Clouds": "☁️ Облачно",
    "Rain": "🌧 Дождь",
    "Drizzle": "🌦 Морось",
    "Thunderstorm": "⛈ Гроза",
    "Snow": "❄️ Снег",
    "Mist": "🌫 Туман",
    "Smoke": "🌫 Дым",
    "Haze": "🌫 Мгла"
}


# Хэндлер инициализации запроса погоды
@router.callback_query(F.data == "cmd_weather")
async def start_weather(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🌤 <b>Погода в городе</b>\n\n"
        "Напишите название города (например: <code>Москва</code> или <code>London</code>).\n"
        "Для выхода из режима отправьте слово <b>отмена</b>.",
        parse_mode="HTML"
    )
    await state.set_state(Level2States.waiting_for_weather_city)
    await callback.answer()


# Хэндлер отправки запроса к OpenWeatherMap API, парсинга ответа и вывода метеосводки
@router.message(Level2States.waiting_for_weather_city)
async def process_weather(message: Message, state: FSMContext):
    city = message.text.strip()
    
    # Обработка ручной отмены операции
    if city.lower() in ["отмена", "/cancel"]:
        await state.clear()
        await message.answer("❌ Запрос погоды отменен.")
        return

    # Формируем URL для запроса (метрическая система, русский язык результатов)
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    
    try:
        # Асинхронно открываем HTTP-сессию
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                if response.status == 404:
                    await message.answer("❌ Город не найден. Проверьте правильность написания и попробуйте еще раз:")
                    return
                elif response.status != 200:
                    await message.answer("❌ Ошибка сервера погоды. Попробуйте позже.")
                    await state.clear()
                    return
                    
                # Пофиксили Scope: парсим JSON строго внутри открытого контекстного менеджера сессии
                data = await response.json()
                
                # Безопасно извлекаем данные из структуры JSON
                city_name = html.quote(data["name"])
                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                humidity = data["main"]["humidity"]
                wind_speed = data["wind"]["speed"]
                weather_main = data["weather"][0]["main"]
                
                # Получаем кастомный эмодзи или берем стандартное описание от API
                status = WEATHER_EMOJIS.get(weather_main, f"✨ {data['weather'][0]['description'].capitalize()}")
                
                text = (
                    f"🌍 <b>Погода в городе {city_name}:</b>\n\n"
                    f"Погода: {status}\n"
                    f"🌡 Температура: <code>{temp:.1f}°C</code> (Ощущается как <code>{feels_like:.1f}°C</code>)\n"
                    f"💧 Влажность: <code>{humidity}%</code>\n"
                    f"💨 Скорость ветра: <code>{wind_speed} м/с</code>"
                )
                
                await message.answer(text, parse_mode="HTML")
                await state.clear()
                
    except Exception as e:
        await message.answer(f"❌ Произошла непредвиденная ошибка: {e}")
        await state.clear()