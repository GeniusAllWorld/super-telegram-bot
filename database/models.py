from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, nullable=True)
    # --- ДОБАВЛЯЕМ СЮДА ---
    is_whitelisted = Column(Boolean, default=False)  # По умолчанию доступ закрыт

class DBTimer(Base):
    __tablename__ = "bot_timers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    chat_id = Column(BigInteger, nullable=False)
    trigger_time = Column(DateTime, nullable=False)  # Когда должен сработать
    minutes = Column(Integer, nullable=True)        # Сколько минут просил юзер
    is_triggered = Column(Boolean, default=False)    # Сработал ли уже?