import os
import platform
import psutil
from aiogram import Router, F
from aiogram.types import CallbackQuery
from config import ADMIN_ID

router = Router()

def make_bar(percent: float) -> str:
    """Создает красивый текстовый прогресс-бар из эмодзи"""
    # 10 делений: каждые 10% — это один кубик
    filled_blocks = int(percent // 10)
    empty_blocks = 10 - filled_blocks
    return "🟩" * filled_blocks + "⬜" * empty_blocks

@router.callback_query(F.data == "cmd_server_monitor")
async def monitor_server(callback: CallbackQuery):
    # Традиционная проверка на админа
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ У вас нет прав для просмотра метрик сервера.", show_alert=True)
        return

    await callback.answer("📊 Собираю системные метрики...")

    # 1. Информация о системе
    os_info = f"{platform.system()} {platform.release()}"
    
    # 2. Нагрузка на процессор (указываем interval=0.5 для замера за полсекунды)
    cpu_usage = psutil.cpu_percent(interval=0.5)
    cpu_bar = make_bar(cpu_usage)
    
    # 3. Оперативная память
    ram = psutil.virtual_memory()
    ram_usage = ram.percent
    ram_bar = make_bar(ram_usage)
    ram_used_gb = ram.used / (1024 ** 3)
    ram_total_gb = ram.total / (1024 ** 3)
    
    # 4. Дисковая память (проверяем корневой раздел)
    disk = psutil.disk_usage('/')
    disk_usage = disk.percent
    disk_bar = make_bar(disk_usage)
    disk_free_gb = disk.free / (1024 ** 3)
    disk_total_gb = disk.total / (1024 ** 3)

    # Собираем всё в один красивый отчет
    report = (
        f"🖥 <b>Мониторинг Сервера</b>\n"
        f"────────────────────\n"
        f"ℹ️ <b>ОС:</b> {os_info}\n"
        f"⏱ <b>Аптайм бота:</b> в работе\n\n"
        
        f"🧠 <b>Загрузка CPU:</b> {cpu_usage}%\n"
        f"{cpu_bar}\n\n"
        
        f"💾 <b>Оперативная память (RAM):</b> {ram_usage}%\n"
        f"{ram_bar}\n"
        f"📊 <i>Использовано: {ram_used_gb:.2f} ГБ из {ram_total_gb:.2f} ГБ</i>\n\n"
        
        f"💽 <b>Дисковое пространство:</b> {disk_usage}%\n"
        f"{disk_bar}\n"
        f"📊 <i>Свободно: {disk_free_gb:.2f} ГБ из {disk_total_gb:.2f} ГБ</i>\n"
        f"────────────────────\n"
        f"🔄 <i>Данные обновлены в реальном времени.</i>"
    )

    await callback.message.answer(report, parse_mode="HTML")