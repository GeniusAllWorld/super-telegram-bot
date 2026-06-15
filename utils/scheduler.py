import os
import logging
import asyncio
import psutil  # Не забудь, что этот импорт теперь переехал сюда
from datetime import datetime
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import ADMIN_ID

# Инициализируем планировщик глобально внутри этого модуля
scheduler = AsyncIOScheduler()

async def send_scheduled_report(bot: Bot):
    """Автоматический сбор статуса сервера и отправка админу (Cron)"""
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


async def restore_timers():
    """Функция восстановления недотикавших таймеров из БД при перезапуске"""
    try:
        from database.db import async_session_maker
        from database.models import DBTimer
        from sqlalchemy import select
        from levels.level2.timer import send_timer_alert
        
        bot_token = os.getenv("BOT_TOKEN")
        
        async with async_session_maker() as session:
            stmt = select(DBTimer).where(DBTimer.is_triggered == False)
            result = await session.execute(stmt)
            active_timers = result.scalars().all()
            
            now = datetime.now()
            count = 0
            
            for timer in active_timers:
                if timer.trigger_time > now:
                    scheduler.add_job(
                        send_timer_alert,
                        trigger='date',
                        run_date=timer.trigger_time,
                        kwargs={
                            "bot_token": bot_token,
                            "chat_id": timer.chat_id,  # Исправил небольшую опечатку timer.chat.id -> timer.chat_id
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


async def init_scheduler(bot: Bot):
    """Полная инициализация, настройка задач и запуск планировщика"""
    scheduler.configure(event_loop=asyncio.get_running_loop())
    
    # --- ДОБАВЛЯЕМ НАШУ CRON ЗАДАЧУ СЮДА ---
    # Будет триггериться каждые 5 минут. Для тестов каждую минуту можно поставить minute='*'
    scheduler.add_job(
        send_scheduled_report,
        trigger='cron',
        minute='*/5',
        kwargs={"bot": bot},
        id="server_health_report",
        replace_existing=True  # Чтобы избежать дублирования при перезапусках в дебаге
    )
    
    scheduler.start()
    logging.info("⏰ [Scheduler] APScheduler привязан к Event Loop и успешно запущен.")
    
    # Сразу запускаем восстановление старых таймеров из БД
    await restore_timers()