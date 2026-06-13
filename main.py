import asyncio
import logging
import importlib
import pkgutil
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

import keyboards.main_menu
# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Динамическая загрузка всех роутеров из папки levels
    import levels
    for loader, module_name, is_pkg in pkgutil.walk_packages(levels.__path__, levels.__name__ + "."):
        module = importlib.import_module(module_name)
        # Проверяем, есть ли в модуле объект router
        if hasattr(module, "router"):
            dp.include_router(module.router) # <--- ВОТ ЗДЕСЬ ИСПРАВЛЕНО
            logging.info(f"Загружен роутер из: {module_name}")

    dp.include_router(keyboards.main_menu.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())