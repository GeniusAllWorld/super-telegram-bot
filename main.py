import asyncio
import logging
import importlib
import pkgutil
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from utils.scheduler import init_scheduler
from utils.web_server import init_web_server

# Импортируем меню заранее, чтобы соблюсти правильный порядок роутеров
import keyboards.main_menu

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logging.getLogger('apscheduler').setLevel(logging.DEBUG)


async def main():
    """
    Основная функция запуска бота.
    Инициализирует сессию Bot и Dispatcher, синхронизирует структуру базы данных,
    автоматически регистрирует все роутеры из папки 'levels', запускает
    фоновые сервисы (планировщик, веб-сервер) и включает режим long-polling.
    """
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Синхронизация таблиц БД (создание, если пустые)
    from database.db import engine
    from database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Сначала подключаем корневые/главные роутеры, чтобы они имели приоритет при хэндлинге
    dp.include_router(keyboards.main_menu.router)

    # Динамическая загрузка всех дочерних роутеров из папки levels
    import levels
    for loader, module_name, is_pkg in pkgutil.walk_packages(levels.__path__, levels.__name__ + "."):
        module = importlib.import_module(module_name)
        if hasattr(module, "router"):
            dp.include_router(module.router)
            logging.info(f"Загружен роутер из: {module_name}")

    # Запускаем изолированный сервис планировщика задач
    await init_scheduler(bot)

    # Запускаем локальный веб-сервер для Telegram Mini Apps
    await init_web_server()
    
    # Запуск бота с гарантированным закрытием сессии при выходе (смягчает остановку)
    try:
        logging.info("Бот успешно запущен и начинает опрос серверов Telegram...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await engine.dispose()  # Чистим за собой пул соединений с БД
        logging.info("Сессии бота и базы данных успешно закрыты.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен пользователем.")