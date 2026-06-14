import aiohttp
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

# URL бесплатного API курсов (обновляется раз в сутки, не требует токенов)
CRYPTO_API_URL = "https://open.er-api.com/v6/latest/USD"

@router.callback_query(F.data == "cmd_currency")
async def currency_converter_handler(callback: CallbackQuery):
    # Создаем кнопку перезапроса курса внутри модуля
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить курс", callback_data="cmd_currency")
    
    try:
        # Асинженно стучимся в API курсов
        async with aiohttp.ClientSession() as session:
            async with session.get(CRYPTO_API_URL, timeout=5) as response:
                if response.status != 200:
                    await callback.message.answer("❌ Не удалось получить данные от сервера курсов валют.")
                    await callback.answer()
                    return
                
                data = await response.json()
                
        # Извлекаем курсы относительно USD
        rates = data.get("rates", {})
        usd_to_rub = rates.get("RUB")
        usd_to_eur = rates.get("EUR")
        
        if not usd_to_rub or not usd_to_eur:
            await callback.message.answer("❌ Ошибка парсинга данных валют.")
            await callback.answer()
            return
            
        # Считаем кросс-курс EUR/RUB
        eur_to_rub = usd_to_rub / usd_to_eur
        
        text = (
            "💱 <b>Актуальный курс валют</b>\n\n"
            f"💵 <b>1 USD</b> = <code>{usd_to_rub:.2f}</code> RUB\n"
            f"💶 <b>1 EUR</b> = <code>{eur_to_rub:.2f}</code> RUB\n"
            f"🇪🇺 <b>1 USD</b> = <code>{usd_to_eur:.4f}</code> EUR\n\n"
            "<i>📊 Данные обновляются автоматически.</i>"
        )
        
        await callback.message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
        
    except Exception as e:
        await callback.message.answer(f"❌ Произошла ошибка при запросе к API: {e}")
        
    finally:
        # Обязательно тушим часики на кнопке в ТГ
        await callback.answer()