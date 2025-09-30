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
    
    @property
    def database_connection_url(self) -> str:
        """Динамический URL базы данных в зависимости от окружения"""
        # Приоритет: переменная окружения -> настройка по умолчанию
        return os.getenv("DATABASE_URL", self.database_url)
    
    # FastAPI
    app_name: str = "Gazprombank Reviews Dashboard API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # CORS - настройки для разработки и продакшена
    environment: str = "development"  # development, staging, production
    
    @property
    def allowed_origins(self) -> list:
        """Динамические CORS origins в зависимости от окружения"""
        base_origins = []
        
        if self.environment == "development":
            base_origins.extend([
                "http://localhost:3000",
                "http://127.0.0.1:3000", 
                "http://localhost:3001",
                "http://127.0.0.1:3001",
                "null"  # Для локальных файлов и тестирования
            ])
        elif self.environment == "staging":
            base_origins.extend([
                "https://gazprombank-dashboard-staging.vercel.app",
                "https://gazprombank-dashboard-staging.herokuapp.com",
                # Добавьте staging домены
            ])
        elif self.environment == "production":
            base_origins.extend([
                "https://gazprombank-dashboard.vercel.app",
                "https://gazprombank-dashboard.herokuapp.com",
                # Добавьте продакшен домены
            ])
        
        # Дополнительные origins из переменной окружения
        env_origins = os.getenv("ADDITIONAL_CORS_ORIGINS", "")
        if env_origins:
            base_origins.extend([origin.strip() for origin in env_origins.split(",")])
            
        return base_origins
    
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
