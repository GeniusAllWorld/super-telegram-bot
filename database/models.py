from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

# Базовый декларативный класс для моделей SQLAlchemy (стандарт SQLAlchemy 2.0)
class Base(DeclarativeBase):
    pass

# Модель пользователя бота для хранения профиля и прав доступа
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, nullable=True)
    is_whitelisted = Column(Boolean, default=False)  # Статус белого списка для админ-панели

# Модель для долгосрочного хранения таймеров и будильников пользователей
class DBTimer(Base):
    __tablename__ = "bot_timers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    chat_id = Column(BigInteger, nullable=False)
    trigger_time = Column(DateTime, nullable=False)  # Точное время планируемого срабатывания
    minutes = Column(Integer, nullable=True)        # Исходный интервал времени в минутах
    is_triggered = Column(Boolean, default=False)    # Флаг завершения задачи планировщиком
    created_at = Column(DateTime, default=datetime.utcnow) # Время создания записи для аналитики