import os
import platform
import psutil
import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery
from config import ADMIN_ID

router = Router()


# Создает текстовый прогресс-бар из эмодзи на основе процента нагрузки
def make_bar(percent: float) -> str:
    # 10 делений: каждые 10% — это один кубик
    filled_blocks = int(percent // 10)
    # Ограничиваем рамки от 0 до 10, на случай скачков метрик выше 100%
    filled_blocks = max(0, min(filled_blocks, 10))
    empty_blocks = 10 - filled_blocks
    return "🟩" * filled_blocks + "⬜" * empty_blocks


# Хэндлер сбора системных метрик сервера без блокировки основного потока бота
@router.callback_query(F.data == "cmd_server_monitor")
async def monitor_server(callback: CallbackQuery):
    # Традиционная жесткая проверка прав на админа
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ У вас нет прав для просмотра метрик сервера.", show_alert=True)
        return

    # Гасим крутилку на кнопке сразу, чтобы показать мгновенный отклик интерфейса
    await callback.answer("📊 Собираю системные метрики...")

    # 1. Информация о текущей операционной системе
    os_info = f"{platform.system()} {platform.release()}"
    
    # 2. ПОФИКСИЛИ БЛОКИРОВКУ: Замер CPU с интервалом выносим в неблокирующий поток asyncio.to_thread
    # Теперь полсекунды ожидания тиков процессора не вешают Event Loop и других пользователей
    cpu_usage = await asyncio.to_thread(psutil.cpu_percent, interval=0.5)
    cpu_bar = make_bar(cpu_usage)
    
    # 3. Оперативная память (RAM)
    ram = psutil.virtual_memory()
    ram_usage = ram.percent
    ram_bar = make_bar(ram_usage)
    ram_used_gb = ram.used / (1024 ** 3)
    ram_total_gb = ram.total / (1024 ** 3)
    
    # 4. ПОФИКСИЛИ КРОССПЛАТФОРМЕННОСТЬ: Динамически выбираем корень в зависимости от ОС (Windows vs Linux)
    root_path = "C:\\" if platform.system() == "Windows" else "/"
    
    try:
        disk = psutil.disk_usage(root_path)
        disk_usage = disk.percent
        disk_bar = make_bar(disk_usage)
        disk_free_gb = disk.free / (1024 ** 3)
        disk_total_gb = disk.total / (1024 ** 3)
        disk_info_text = (
            f"💽 <b>Дисковое пространство:</b> {disk_usage}%\n"
            f"{disk_bar}\n"
            f"📊 <i>Свободно: {disk_free_gb:.2f} ГБ из {disk_total_gb:.2f} ГБ</i>\n"
        )
    except Exception:
        disk_info_text = "💽 <b>Дисковое пространство:</b> <i>Не удалось определить разделы</i>\n"

    # Собираем все метрики в единый читаемый HTML-отчет
    report = (
        f"🖥 <b>Мониторинг Сервера</b>\n"
        f"────────────────────\n"
        f"ℹ️ <b>ОС:</b> {os_info}\n\n"
        
        f"🧠 <b>Загрузка CPU:</b> {cpu_usage}%\n"
        f"{cpu_bar}\n\n"
        
        f"💾 <b>Оперативная память (RAM):</b> {ram_usage}%\n"
        f"{ram_bar}\n"
        f"📊 <i>Использовано: {ram_used_gb:.2f} ГБ из {ram_total_gb:.2f} ГБ</i>\n\n"
        
        f"{disk_info_text}"
        f"────────────────────\n"
        f"🔄 <i>Данные успешно обновлены.</i>"
    )

    await callback.message.answer(report, parse_mode="HTML")