from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level2States
from utils.scheduler import scheduler

from database.models import DBTimer
from database.db import async_session_maker
from levels.level2.timer import send_timer_alert # Переиспользуем функцию отправки!
from config import BOT_TOKEN

router = Router()

@router.callback_query(F.data == "cmd_alarm")
async def start_alarm(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "⏰ <b>Установка будильника</b>\n\n"
        "Введите дату, когда должен сработать будильник, в формате <code>ДД.ММ.ГГГГ</code>\n"
        "Например: <code>14.06.2026</code>",
        parse_mode="HTML"
    )
    await state.set_state(Level2States.waiting_for_alarm_date)
    await callback.answer()


@router.message(Level2States.waiting_for_alarm_date)
async def process_alarm_date(message: Message, state: FSMContext):
    date_text = message.text.strip()
    
    # Проверяем корректность формата даты
    try:
        valid_date = datetime.strptime(date_text, "%d.%m.%Y")
        # Сохраняем чистую строку даты во временное хранилище FSM
        await state.update_data(alarm_date=date_text)
        
        await message.answer(
            "⏳ Отлично! Теперь введите время в формате <code>ЧЧ:ММ</code>\n"
            "Например: <code>11:30</code>",
            parse_mode="HTML"
        )
        await state.set_state(Level2States.waiting_for_alarm_time)
        
    except ValueError:
        await message.answer("❌ Неверный формат даты! Пожалуйста, введите дату строго в формате <code>ДД.ММ.ГГГГ</code> (например: 14.06.2026):", parse_mode="HTML")


@router.message(Level2States.waiting_for_alarm_time)
async def process_alarm_time(message: Message, state: FSMContext):
    time_text = message.text.strip()
    
    # Достаем ранее введенную дату из FSM
    user_data = await state.get_data()
    date_text = user_data.get("alarm_date")
    
    # Пробуем собрать полноценную дату и время вместе
    try:
        full_datetime_str = f"{date_text} {time_text}"
        trigger_time = datetime.strptime(full_datetime_str, "%d.%m.%Y %H:%M")
        
        # Проверяем, не в прошлом ли это время
        if trigger_time < datetime.now():
            await message.answer("❌ Упс! Это время уже прошло. Введите корректное время в будущем (ЧЧ:ММ):")
            return
            
    except ValueError:
        await message.answer("❌ Неверный формат времени! Пожалуйста, введите время строго в формате <code>ЧЧ:ММ</code> (например: 11:30):", parse_mode="HTML")
        return

    # Если всё ок — пишем в БД и шедулер
    try:
        # 1. Запись в БД (используем ту же таблицу)
        async with async_session_maker() as session:
            async with session.begin():
                new_alarm = DBTimer(
                    user_id=message.from_user.id,
                    chat_id=message.chat.id,
                    trigger_time=trigger_time,
                    minutes=None # Для будильника минуты не заполняем
                )
                session.add(new_alarm)
                await session.flush()
                alarm_id = new_alarm.id

        # 2. Добавление задачи в APScheduler
        scheduler.add_job(
            send_timer_alert,
            trigger='date',
            run_date=trigger_time,
            kwargs={
                "bot_token": BOT_TOKEN,
                "chat_id": message.chat.id,
                "user_id": message.from_user.id,
                "minutes": 0, # Передаем 0 или можно кастомизировать текст алерта
                "timer_id": alarm_id
            },
            id=f"timer_{alarm_id}" # Используем тот же префикс, чтобы restore_timers в main подхватил его при перезапуске
        )
        
        await message.answer(
            f"🔔 <b>Будильник успешно установлен!</b>\n\n"
            f"📅 Дата: <code>{date_text}</code>\n"
            f"⏰ Время: <code>{time_text}</code>\n\n"
            f"<i>Бот обязательно пришлет вам уведомление в указанное время.</i>",
            parse_mode="HTML"
        )
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Не удалось установить будильник. Ошибка: {e}")
        await state.clear()