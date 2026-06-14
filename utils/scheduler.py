import os
import logging
import asyncio
from datetime import datetime
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()

# Инициализируем планировщик глобально внутри этого модуля
scheduler = AsyncIOScheduler()

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
                            "chat_id": timer.chat.id,
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


async def init_scheduler():
    """Полная инициализация и запуск планировщика в текущем Event Loop"""
    scheduler.configure(event_loop=asyncio.get_running_loop())
    scheduler.start()
    logging.info("⏰ [Scheduler] APScheduler привязан к Event Loop и успешно запущен.")
    
    # Сразу запускаем восстановление старых таймеров
    await restore_timers()