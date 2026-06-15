import os
from aiogram import Router, F
from aiogram.types import CallbackQuery
from utils.scheduler import scheduler

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

@router.callback_query(F.data == "cmd_cron_scheduler")
async def check_scheduler_status(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Доступ запрещен!", show_alert=True)
        return

    jobs = scheduler.get_jobs()
    
    text = "⏳ <b>Планировщик задач (APScheduler)</b>\n\n"
    text += f"Статус планировщика: <b>{'Запущен' if scheduler.running else 'Остановлен'}</b>\n\n"
    
    if not jobs:
        text += "<i>Активных задач по расписанию пока нет.</i>"
    else:
        text += "<b>Текущие задачи:</b>\n"
        for idx, job in enumerate(jobs, 1):
            text += f"{idx}. 🆔 <code>{job.id}</code> — Следующий запуск: <code>{job.next_run_time}</code>\n"

    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()