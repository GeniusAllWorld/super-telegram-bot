import asyncio
from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level2States

from database.models import DBTimer
from database.db import async_session_maker
from utils.scheduler import scheduler

router = Router()


# Независимая асинхронная функция-алерт для отправки уведомлений по таймеру
async def send_timer_alert(bot_token: str, chat_id: int, user_id: int, minutes: int, timer_id: int):
    try:
        if minutes > 0:
            text = f"⏳ <b>Внимание!</b>\n\nПрошло <code>{minutes}</code> мин. Ваш таймер подошел к концу!"
        else:
            text = f"🔔 <b>Будильник!</b>\n\nВремя пришло! Пора просыпаться или делать важные дела."
            
        # Создаем временный изолированный контекст бота для безопасной отправки пакета
        async with Bot(token=bot_token) as bot:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="HTML"
            )
        
        # Переключаем статус триггера в базе данных на True
        async with async_session_maker() as session:
            async with session.begin():
                from sqlalchemy import update
                stmt = update(DBTimer).where(DBTimer.id == timer_id).values(is_triggered=True)
                await session.execute(stmt)
                
    except Exception as e:
        print(f"Ошибка отправки таймера {timer_id}: {e}")


# Хэндлер инициализации таймера напоминаний
@router.callback_query(F.data == "cmd_timer")
async def start_timer(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "⏳ <b>Установка таймера</b>\n\n"
        "Через сколько минут вам напомнить? Введите целое число (например: 5).\n"
        "Для отмены операции напишите <b>отмена</b>.",
        parse_mode="HTML"
    )
    await state.set_state(Level2States.waiting_for_timer_time)
    await callback.answer()


# Хэндлер валидации ввода, расчета времени срабатывания и регистрации задачи
@router.message(Level2States.waiting_for_timer_time)
async def process_timer(message: Message, state: FSMContext):
    text = message.text.strip()
    
    # Обработка ручной отмены операции
    if text.lower() in ["отмена", "/cancel"]:
        await state.clear()
        await message.answer("❌ Установка таймера отменена.")
        return
        
    # Проверка на корректность ввода числового значения
    if not text.isdigit() or int(text) <= 0:
        await message.answer("❌ Пожалуйста, введите целое положительное число минут:")
        return
        
    # Защита от OverflowError: ограничиваем максимальный период таймера 30 днями
    if len(text) > 5 or int(text) > 43200:
        await message.answer("❌ Слишком долгий таймер! Максимальный срок установки — 43200 минут (30 дней).")
        return
        
    # Пофиксили: вынесли инициализацию переменной на правильный уровень отступов
    minutes = int(text)

    # Пофиксили отступы: теперь этот блок находится строго внутри функции process_timer
    # Для APScheduler нам ОБЯЗАТЕЛЬНО нужен aware-объект с таймзоной
    trigger_time_tz = datetime.now(scheduler.timezone) + timedelta(minutes=minutes)

    # А для базы данных (TIMESTAMP WITHOUT TIME ZONE) мы делаем копию БЕЗ таймзоны
    trigger_time_db = trigger_time_tz.replace(tzinfo=None)

    try:
        # 1. Сохраняем метаданные таймера в реляционную базу данных
        async with async_session_maker() as session:
            async with session.begin():
                new_timer = DBTimer(
                    user_id=message.from_user.id,
                    chat_id=message.chat.id,
                    trigger_time=trigger_time_db,  # Передаем наивное время без tz
                    minutes=minutes
                )
                session.add(new_timer)
                await session.flush()
                timer_id = new_timer.id

        # 2. Регистрируем задачу в планировщике (сюда передаем время С ТАЙМЗОНОЙ)
        from config import BOT_TOKEN
        scheduler.add_job(
            send_timer_alert,
            trigger='date',
            run_date=trigger_time_tz,  # Оставляем aware объект для стабильности APScheduler
            kwargs={
                "bot_token": BOT_TOKEN,
                "chat_id": message.chat.id,
                "user_id": message.from_user.id,
                "minutes": minutes,
                "timer_id": timer_id
            },
            id=f"timer_{timer_id}"
        )
        
        # Пофиксили: заменили упавшую переменную trigger_time на trigger_time_tz
        await message.answer(
            f"✅ <b>Таймер успешно запущен!</b>\n\n"
            f"Бот напомнит вам обо всем через <code>{minutes}</code> мин. "
            f"(⏱ Время срабатывания: <code>{trigger_time_tz.strftime('%H:%M:%S')}</code>)",
            parse_mode="HTML"
        )
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Не удалось запустить таймер. Ошибка: {e}")
        await state.clear()