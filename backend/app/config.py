"""
Конфигурация приложения
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # База данных
    database_url: str = "postgresql://postgres:postgres@localhost:5432/gazprombank_reviews"
    
    # FastAPI
    app_name: str = "Gazprombank Reviews Dashboard API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # CORS
    allowed_origins: list = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ]
    
    # Пагинация
    default_page_size: int = 50
    max_page_size: int = 1000
    
    # Данные
    data_path: str = "/app/data/raw/banki_ru"  # Путь внутри Docker контейнера
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Глобальный экземпляр настроек
settings = Settings()
