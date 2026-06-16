import os
import logging
import asyncio
import psutil
from datetime import datetime
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import ADMIN_ID

# Инициализируем планировщик глобально внутри этого модуля
scheduler = AsyncIOScheduler()

# Автоматический сбор статуса сервера и отправка админу (Cron)
async def send_scheduled_report(bot: Bot):
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    
    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"⏰ <b>Автоматический отчет по расписанию (Cron)</b>\n\n"
                 f"🖥 Нагрузка процессора: <code>{cpu}%</code>\n"
                 f"🧠 Занято оперативки: <code>{ram}%</code>\n"
                 f"<i>Проверка выполнена успешно!</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"❌ [Scheduler] Ошибка отправки cron-отчета: {e}")

# Функция восстановления недотикавших таймеров из БД при перезапуске бота
async def restore_timers(bot: Bot):
    try:
        from database.db import async_session_maker
        from database.models import DBTimer
        from sqlalchemy import select
        from levels.level2.timer import send_timer_alert
        
        async with async_session_maker() as session:
            # Выбираем только те таймеры, которые еще не сработали
            stmt = select(DBTimer).where(DBTimer.is_triggered == False)
            result = await session.execute(stmt)
            active_timers = result.scalars().all()
            
            now = datetime.now()
            count = 0
            
            for timer in active_timers:
                # Если время таймера еще не наступило, пересоздаем задачу в APScheduler
                if timer.trigger_time > now:
                    scheduler.add_job(
                        send_timer_alert,
                        trigger='date',
                        run_date=timer.trigger_time,
                        kwargs={
                            "bot": bot,  # Исправлено: передаем живой объект bot вместо строки токена
                            "chat_id": timer.chat_id,
                            "user_id": timer.user_id,
                            "minutes": timer.minutes,
                            "timer_id": timer.id
                        },
                        id=f"timer_{timer.id}"
                    )
                    count += 1
            
            if count > 0:
                logging.info(f"⏰ [Scheduler] Успешно восстановлено таймеров из БД: {count}")
                
    except Exception as e:
        logging.error(f"❌ [Scheduler] Ошибка при восстановлении таймеров: {e}")

# Полная инициализация, настройка задач и запуск планировщика
async def init_scheduler(bot: Bot):
    scheduler.configure(event_loop=asyncio.get_running_loop())
    
    # Настройка Cron-задачи на отправку отчетов каждые 5 минут
    scheduler.add_job(
        send_scheduled_report,
        trigger='cron',
        hour='*/1',
        kwargs={"bot": bot},
        id="server_health_report",
        replace_existing=True  # Предотвращает дублирование задачи при перезапуске кода
    )
    
    scheduler.start()
    logging.info("⏰ [Scheduler] APScheduler привязан к Event Loop и успешно запущен.")
    
    # Запускаем восстановление, передавая объект бота внутрь
    await restore_timers(bot)