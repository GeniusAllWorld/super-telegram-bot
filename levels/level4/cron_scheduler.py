import os
from aiogram import Router, F
from aiogram.types import CallbackQuery
from utils.scheduler import scheduler
from config import ADMIN_ID

router = Router()


# Хэндлер мониторинга фоновых задач планировщика APScheduler
@router.callback_query(F.data == "cmd_cron_scheduler")
async def check_scheduler_status(callback: CallbackQuery):
    # Проверка прав доступа: только для главного администратора
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return

    # Получаем список всех зарегистрированных тасок в Event Loop планировщика
    jobs = scheduler.get_jobs()
    
    # Определяем статус работы самого планировщика
    status_text = "🟢 Запущен" if scheduler.running else "🔴 Остановлен"
    
    text = (
        f"⏳ <b>Планировщик задач (APScheduler)</b>\n\n"
        f"📊 Статус ядра: <b>{status_text}</b>\n"
        f"🕒 Всего задач в пуле: <code>{len(jobs)}</code>\n\n"
    )
    
    if not jobs:
        text += "<i>Активных задач по расписанию пока нет.</i>"
    else:
        text += "<b>Текущие фоновые процессы:</b>\n"
        for idx, job in enumerate(jobs, 1):
            # ПОФИКСИЛИ БАГ NONE: Безопасно обрабатываем задачи без времени следующего запуска (например, на паузе)
            if job.next_run_time:
                # Форматируем дату в удобный для чтения формат ДД.ММ.ГГГГ ЧЧ:ММ:СС
                next_run = job.next_run_time.strftime("%d.%m.%Y %H:%M:%S")
            else:
                next_run = "Приостановлена ⏸"
                
            text += f"{idx}. 🆔 <code>{job.id}</code>\n     ↳ След. запуск: <code>{next_run}</code>\n"

    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()