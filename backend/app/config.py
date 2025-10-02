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
    
    # Дополнительные CORS origins
    additional_cors_origins: str = ""

    # Пагинация
    default_page_size: int = 50
    max_page_size: int = 1000

    # Данные
    data_path: str = "/app/data/raw"

    @property
    def database_connection_url(self) -> str:
        return os.getenv("DATABASE_URL", self.database_url)
    
    # FastAPI
    app_name: str = "Gazprombank Reviews Dashboard API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # CORS - настройки
    environment: str = "development"  # development, staging, production
    
    @property
    def allowed_origins(self) -> list:
        base_origins = []
        
        if self.environment == "development":
            base_origins.extend([
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "null"
            ])
        elif self.environment == "staging":
            base_origins.extend([
                "https://gazprombank-dashboard-staging.vercel.app",
                "https://gazprombank-dashboard-staging.herokuapp.com",
            ])
        elif self.environment == "production":
            base_origins.extend([
                "https://gazprombank-dashboard.vercel.app",
                "https://gazprombank-dashboard.herokuapp.com",
            ])
        
        # Поддержка .env ADDITIONAL_CORS_ORIGINS
        if self.additional_cors_origins:
            base_origins.extend([
                origin.strip() for origin in self.additional_cors_origins.split(",")
            ])
        
        return base_origins
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Глобальный экземпляр настроек
print("ENV VARS:", {k: v for k, v in os.environ.items() if "CORS" in k})
settings = Settings()
print("✅ Allowed origins:", settings.allowed_origins)
