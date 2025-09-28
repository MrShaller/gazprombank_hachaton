"""
Главное FastAPI приложение для дашборда отзывов Газпромбанка
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import traceback

from .config import settings
from .database import create_tables
from .routers import products, reviews, analytics, predict

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    🏦 **API для дашборда анализа отзывов Газпромбанка**
    
    Этот API предоставляет данные для анализа клиентских отзывов о продуктах и услугах Газпромбанка.
    
    ## Основные возможности:
    
    * **Продукты** - получение списка продуктов/услуг с базовой статистикой
    * **Отзывы** - работа с отзывами клиентов (фильтрация, поиск)  
    * **Аналитика** - анализ тональностей, динамика по времени, рейтинги
    
    ## Фильтрация:
    
    * По продуктам/услугам
    * По тональности (положительно/отрицательно/нейтрально)
    * По временным интервалам
    * По рейтингам
    
    ## Временные интервалы:
    
    Поддерживается группировка данных по дням, неделям и месяцам для анализа динамики.
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(products.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(predict.router, prefix="/api/v1")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Глобальный обработчик исключений"""
    logger.error(f"Необработанная ошибка: {exc}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Внутренняя ошибка сервера",
            "detail": str(exc) if settings.debug else "Обратитесь к администратору"
        }
    )


@app.on_event("startup")
async def startup_event():
    """События при запуске приложения"""
    logger.info(f"Запуск {settings.app_name} v{settings.app_version}")
    
    try:
        # Создание таблиц БД (если не существуют)
        create_tables()
        logger.info("Таблицы базы данных проверены/созданы")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """События при остановке приложения"""
    logger.info("Остановка приложения")


@app.get("/", tags=["root"])
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "🏦 Gazprombank Reviews Dashboard API",
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Проверка здоровья приложения"""
    try:
        # Здесь можно добавить проверки БД, внешних сервисов и т.д.
        return {
            "status": "healthy",
            "version": settings.app_version,
            "database": "connected"  # В реальности нужно проверить подключение
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.get("/api/v1/health", tags=["health"])
async def api_health_check():
    """Проверка здоровья API"""
    try:
        return {
            "status": "healthy",
            "version": settings.app_version,
            "database": "connected",
            "api": "v1"
        }
    except Exception as e:
        logger.error(f"API Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/api/v1/info", tags=["info"])
async def api_info():
    """Информация об API"""
    return {
        "api_version": "v1",
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "endpoints": {
            "products": "/api/v1/products",
            "reviews": "/api/v1/reviews", 
            "analytics": "/api/v1/analytics"
        },
        "features": [
            "Список продуктов с статистикой",
            "Фильтрация отзывов",
            "Анализ тональностей",
            "Динамика по времени",
            "Распределение рейтингов",
            "Топ отзывы"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
