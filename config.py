from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
WEATHER_API_KEY=os.getenv("WEATHER_API_KEY")
DATABASE_URL=os.getenv("DATABASE_URL")
GIPHY_API_KEY=os.getenv("GIPHY_API_KEY")

BOT_VERSION = "3.1.0"
BUILD_DATE = "13.06.2026"