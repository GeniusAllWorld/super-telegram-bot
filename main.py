import asyncio
import logging
import importlib
import pkgutil
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from utils.scheduler import init_scheduler  # Импортируем наш инициализатор

import keyboards.main_menu

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logging.getLogger('apscheduler').setLevel(logging.DEBUG)  # Оставляем дебаг для проверки

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Синхронизация таблиц БД
    from database.db import engine
    from database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Динамическая загрузка всех роутеров из папки levels
    import levels
    for loader, module_name, is_pkg in pkgutil.walk_packages(levels.__path__, levels.__name__ + "."):
        module = importlib.import_module(module_name)
        if hasattr(module, "router"):
            dp.include_router(module.router)
            logging.info(f"Загружен роутер из: {module_name}")

    dp.include_router(keyboards.main_menu.router)

    # Запускаем изолированный сервис планировщика
    await init_scheduler(bot)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())