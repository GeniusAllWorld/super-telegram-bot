from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

BOT_VERSION = "1.0.0"
BUILD_DATE = "13.06.2026"