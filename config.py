import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

#Конфигурация API-ключей и токенов для интеграции с внешними сервисами.

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")
AI_API_KEY = os.getenv("AI_API_KEY")
OCR_API_KEY = os.getenv("OCR_API_KEY")


#Системные настройки проекта: доступы администратора, базы данных, путей и веб-ресурсов.

# Безопасное приведение к int со значением по умолчанию 0, чтобы избежать TypeError
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
DATABASE_URL = os.getenv("DATABASE_URL")
FFMPEG_PATH = os.getenv("FFMPEG_PATH")
GITHUB_REPO = os.getenv("GITHUB_REPO")
WEBAPP_URL = os.getenv("WEBAPP_URL")


#Метаданные текущей сборки приложения (версия и дата релиза).

BOT_VERSION = "5.4.0"
BUILD_DATE = "16.06.2026"