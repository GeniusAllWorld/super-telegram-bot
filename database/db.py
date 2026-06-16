from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import DATABASE_URL  # Используем централизованный конфиг

if not DATABASE_URL:
    raise ValueError("❌ Критическая ошибка: DATABASE_URL не задан в конфигурации приложения!")

# Автоматически адаптируем строку подключения под асинхронные драйверы
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif DATABASE_URL.startswith("sqlite://"):
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")

#Инициализация асинхронного движка SQLAlchemy Engine.
#Настраивает параметры пула соединений для стабильной работы под высокой нагрузкой.
engine = create_async_engine(
    DATABASE_URL, 
    echo=False,
    # Параметры пула (актуально для PostgreSQL, предотвращает нехватку соединений)
    pool_size=20,          # Базовое количество удерживаемых соединений
    max_overflow=10,       # Сколько дополнительных соединений можно открыть при пиковой нагрузке
    pool_recycle=3600      # Сбрасываем старые соединения раз в час, чтобы их не рвал сервер
)

#Фабрика асинхронных сессий (Sessionmaker).
#Используется для генерации изолированных сессий базы данных в хэндлерах и сервисах.
async_session_maker = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)