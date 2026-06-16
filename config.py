from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
WEATHER_API_KEY=os.getenv("WEATHER_API_KEY")
DATABASE_URL=os.getenv("DATABASE_URL")
GIPHY_API_KEY=os.getenv("GIPHY_API_KEY")
FFMPEG_PATH=os.getenv("FFMPEG_PATH")
GITHUB_REPO=os.getenv("GITHUB_REPO")
AI_API_KEY=os.getenv("AI_API_KEY")
OCR_API_KEY=os.getenv("OCR_API_KEY")
WEBAPP_URL=os.getenv("WEBAPP_URL")

BOT_VERSION = "5.0.0"
BUILD_DATE = "15.06.2026"