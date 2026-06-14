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

# Изменили: теперь мы передаем сам bot_id, чтобы внутри функции достать объект бота
async def send_timer_alert(bot_token: str, chat_id: int, user_id: int, minutes: int, timer_id: int):
    try:
        # В файле levels/level2/timer.py внутри функции send_timer_alert:
        if minutes > 0:
            text = f"⏰ <b>Внимание!</b>\n\nПрошло <code>{minutes}</code> мин. Ваш таймер подошел к концу!"
        else:
            text = f"🔔 <b>Будильник!</b>\n\nВремя пришло! Пора просыпаться или делать важные дела."
        # Создаем временный локальный объект бота для отправки сообщения
        async with Bot(token=bot_token) as bot:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="HTML"
            )
        
        # Помечаем в БД, что таймер успешно сработал
        async with async_session_maker() as session:
            async with session.begin():
                from sqlalchemy import update
                stmt = update(DBTimer).where(DBTimer.id == timer_id).values(is_triggered=True)
                await session.execute(stmt)
                
    except Exception as e:
        print(f"Ошибка отправки таймера {timer_id}: {e}")


@router.callback_query(F.data == "cmd_timer")
async def start_timer(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "⏳ <b>Установка таймера</b>\n\n"
        "Через сколько минут вам напомнить? Введите целое число (например: 1):",
        parse_mode="HTML"
    )
    await state.set_state(Level2States.waiting_for_timer_time)
    await callback.answer()


@router.message(Level2States.waiting_for_timer_time)
async def process_timer(message: Message, state: FSMContext):
    text = message.text.strip()
    
    if not text.isdigit() or int(text) <= 0:
        await message.answer("❌ Пожалуйста, введите целое положительное число минут:")
        return
        
    minutes = int(text)
    # Берем чистое локальное время компьютера
    trigger_time = datetime.now()
    trigger_time = trigger_time + timedelta(minutes=minutes)
    
    try:
        # 1. Сохраняем таймер в базу данных
        async with async_session_maker() as session:
            async with session.begin():
                new_timer = DBTimer(
                    user_id=message.from_user.id,
                    chat_id=message.chat.id,
                    trigger_time=trigger_time,
                    minutes=minutes
                )
                session.add(new_timer)
                await session.flush()
                timer_id = new_timer.id

        # 2. Закидываем задачу в асинхронный APScheduler
        from config import BOT_TOKEN
        scheduler.add_job(
            send_timer_alert,
            trigger='date',
            run_date=trigger_time,
            kwargs={
                "bot_token": BOT_TOKEN,
                "chat_id": message.chat.id,
                "user_id": message.from_user.id,
                "minutes": minutes,
                "timer_id": timer_id
            },
            id=f"timer_{timer_id}"
        )
        
        await message.answer(
            f"✅ <b>Таймер успешно запущен!</b>\n\n"
            f"Бот напомнит вам обо всем через <code>{minutes}</code> мин. ({trigger_time.strftime('%H:%M:%S')})",
            parse_mode="HTML"
        )
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Не удалось запустить таймер. Ошибка: {e}")
        await state.clear()