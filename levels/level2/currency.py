import aiohttp
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

# URL бесплатного API курсов (обновляется раз в сутки, не требует токенов)
CRYPTO_API_URL = "https://open.er-api.com/v6/latest/USD"

# Хэндлер обработки запроса и обновления курса валют
@router.callback_query(F.data == "cmd_currency")
async def currency_converter_handler(callback: CallbackQuery):
    # Создаем инлайн-кнопку для обновления данных
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить курс", callback_data="cmd_currency")
    
    try:
        # Асинхронно открываем сессию для HTTP-запроса
        async with aiohttp.ClientSession() as session:
            async with session.get(CRYPTO_API_URL, timeout=5) as response:
                if response.status != 200:
                    await callback.message.answer("❌ Не удалось получить данные от сервера курсов валют.")
                    return
                
                # Пофиксили: читаем и парсим JSON строго внутри контекстного менеджера
                data = await response.json()
                
                # Извлекаем курсы относительно базовой валюты (USD)
                rates = data.get("rates", {})
                usd_to_rub = rates.get("RUB")
                usd_to_eur = rates.get("EUR")
                
                if not usd_to_rub or not usd_to_eur:
                    await callback.message.answer("❌ Ошибка парсинга данных валют.")
                    return
                
                # Вычисляем кросс-курс евро к рублю
                eur_to_rub = usd_to_rub / usd_to_eur
                
                text = (
                    "💱 <b>Актуальный курс валют</b>\n\n"
                    f"💵 <b>1 USD</b> = <code>{usd_to_rub:.2f}</code> RUB\n"
                    f"開設 <b>1 EUR</b> = <code>{eur_to_rub:.2f}</code> RUB\n"
                    f"🇪🇺 <b>1 USD</b> = <code>{usd_to_eur:.4f}</code> EUR\n\n"
                    f"<i>📊 Данные обновляются динамически.</i>"
                )
                
                # Пофиксили UX: Изменяем текущее сообщение вместо отправки нового, чтобы избежать флуда
                try:
                    await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=builder.as_markup())
                except Exception:
                    # Защита на случай, если курс не изменился и Telegram вернет ошибку "message is not modified"
                    pass
        
    except Exception as e:
        await callback.message.answer(f"❌ Произошла ошибка при запросе к API: {e}")
        
    finally:
        # Гасим индикатор загрузки ("часики") на инлайн-кнопке
        await callback.answer()