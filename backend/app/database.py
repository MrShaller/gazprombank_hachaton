"""
Конфигурация базы данных и сессий SQLAlchemy
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

# Настройки подключения к PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/gazprombank_reviews"
)

# Создание движка SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_recycle=300,    # Переподключение каждые 5 минут
    echo=False           # Логирование SQL запросов (для отладки установить True)
)

# Фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()


def get_db() -> Generator:
    """
    Генератор сессий базы данных для использования в FastAPI
    
    Yields:
        Session: Сессия SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Создание всех таблиц в базе данных"""
    from .models import Base
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Удаление всех таблиц (для разработки)"""
    from .models import Base
    Base.metadata.drop_all(bind=engine)
