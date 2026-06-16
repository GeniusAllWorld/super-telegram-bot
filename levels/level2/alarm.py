from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from utils.states import Level2States
from utils.scheduler import scheduler

from database.models import DBTimer
from database.db import async_session_maker
from levels.level2.timer import send_timer_alert
from config import BOT_TOKEN

router = Router()


# Хэндлер нажатия на инлайн-кнопку установки будильника
@router.callback_query(F.data == "cmd_alarm")
async def start_alarm(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "⏰ <b>Установка будильника</b>\n\n"
        "Введите дату, когда должен сработать будильник, в формате <code>ДД.ММ.ГГГГ</code>\n"
        "Например: <code>16.06.2026</code>\n"
        "Для отмены операции напишите <b>отмена</b>.",
        parse_mode="HTML"
    )
    await state.set_state(Level2States.waiting_for_alarm_date)
    await callback.answer()


# Хэндлер обработки и валидации введенной пользователем даты
@router.message(Level2States.waiting_for_alarm_date)
async def process_alarm_date(message: Message, state: FSMContext):
    date_text = message.text.strip()
    
    # Обработка ручной отмены операции
    if date_text.lower() in ["отмена", "/cancel"]:
        await state.clear()
        await message.answer("❌ Установка будильника отменена.")
        return
    
    try:
        # Проверяем корректность формата даты
        datetime.strptime(date_text, "%d.%m.%Y")
        
        # Сохраняем чистую строку даты во временное хранилище FSM
        await state.update_data(alarm_date=date_text)
        
        await message.answer(
            "⏳ Отлично! Теперь введите время в формате <code>ЧЧ:ММ</code>\n"
            "Например: <code>15:30</code>",
            parse_mode="HTML"
        )
        await state.set_state(Level2States.waiting_for_alarm_time)
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты! Пожалуйста, введите дату строго в формате <code>ДД.ММ.ГГГГ</code>:", 
            parse_mode="HTML"
        )


# Хэндлер обработки времени, сборки финального datetime объекта и постановки таски в шедулер
@router.message(Level2States.waiting_for_alarm_time)
async def process_alarm_time(message: Message, state: FSMContext):
    time_text = message.text.strip()
    
    # Обработка ручной отмены операции
    if time_text.lower() in ["отмена", "/cancel"]:
        await state.clear()
        await message.answer("❌ Установка будильника отменена.")
        return
    
    # Достаем ранее введенную дату из FSM
    user_data = await state.get_data()
    date_text = user_data.get("alarm_date")
    
    # ПОФИКСИЛИ NameError: собираем финальную строку для парсинга из даты и времени
    full_datetime_str = f"{date_text} {time_text}"
    
    try:
        # Переводим склеенную строку в наивный datetime объект
        naive_time = datetime.strptime(full_datetime_str, "%d.%m.%Y %H:%M")
        
        # Присваиваем объекту таймзону планировщика (aware datetime) для корректной работы шедулера
        trigger_time_tz = naive_time.replace(tzinfo=scheduler.timezone)

        # Делаем копию для базы данных без tz info (для TIMESTAMP WITHOUT TIME ZONE)
        trigger_time_db = trigger_time_tz.replace(tzinfo=None)

        # Получаем текущее время с таймзоной для сверки
        now_with_tz = datetime.now(scheduler.timezone)

        # Проверяем, не пытается ли пользователь установить будильник в прошлое
        if trigger_time_tz < now_with_tz:
            await message.answer("❌ Упс! Это время уже прошло. Введите корректное время в будущем (ЧЧ:ММ):")
            return
            
    except ValueError:
        # ПОФИКСИЛИ UX: обрабатываем ошибку некорректного ввода времени, возвращая юзеру фидбек
        await message.answer("❌ Неверный формат времени! Пожалуйста, введите время в формате <code>ЧЧ:ММ</code> (например, 18:45):", parse_mode="HTML")
        return

    try:
        # 1. Запись в реляционную БД транзакционным методом
        async with async_session_maker() as session:
            async with session.begin():
                new_alarm = DBTimer(
                    user_id=message.from_user.id,
                    chat_id=message.chat.id,
                    trigger_time=trigger_time_db,  # Улетает чистый datetime без tz, база счастлива
                    minutes=None
                )
                session.add(new_alarm)
                await session.flush()
                alarm_id = new_alarm.id

        # 2. Постановка фоновой задачи в APScheduler
        scheduler.add_job(
            send_timer_alert,
            trigger='date',
            run_date=trigger_time_tz,  # Передаем объект с часовым поясом для точного выстрела
            kwargs={
                "bot_token": BOT_TOKEN,
                "chat_id": message.chat.id,
                "user_id": message.from_user.id,
                "minutes": 0,
                "timer_id": alarm_id
            },
            id=f"timer_{alarm_id}"
        )
    
        await message.answer(
            f"🔔 <b>Будильник успешно установлен!</b>\n\n"
            f"📅 Дата: <code>{date_text}</code>\n"
            f"⏰ Время: <code>{time_text}</code>\n\n"
            f"<i>Бот пришлет вам уведомление точно в указанный срок.</i>",
            parse_mode="HTML"
        )
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Не удалось установить будильник. Ошибка: {e}")
        await state.clear()