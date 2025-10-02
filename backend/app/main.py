"""
Главное FastAPI приложение для дашборда отзывов Газпромбанка
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
import traceback

from .config import settings
from .database import create_tables
from .routers import products, reviews, analytics, predict, aspects
from .routers.predict import get_pipeline

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
    force=True,
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
    """,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Подключение роутеров с префиксами
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(reviews.router, prefix="/api/v1/reviews", tags=["reviews"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(predict.router, prefix="/api/v1/predict", tags=["predict"])
app.include_router(aspects.router, prefix="/api/v1/aspects", tags=["aspects"])

# Глобальный обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Необработанная ошибка: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "error": "Внутренняя ошибка сервера",
            "detail": str(exc) if settings.debug else "Обратитесь к администратору"
        }
    )

# События при запуске/остановке
@app.on_event("startup")
async def startup_event():
    logger.info(f"Запуск {settings.app_name} v{settings.app_version}")
    try:
        create_tables()
        logger.info("Таблицы базы данных проверены/созданы")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        raise
    
    # Инициализация ML пайплайна при старте приложения
    logger.info("Инициализация ML моделей...")
    try:
        pipeline = get_pipeline()
        if pipeline is not None:
            logger.info("✅ ML модели успешно загружены при старте приложения")
        else:
            logger.warning("⚠️ ML модели не удалось загрузить, будет использоваться fallback")
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке ML моделей: {e}")
        logger.info("Приложение продолжит работу без ML моделей (fallback режим)")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Остановка приложения")

# Корневой эндпоинт (просто справка)
@app.get("/", tags=["root"])
async def root():
    return {
        "message": "🏦 Gazprombank Reviews Dashboard API",
        "version": settings.app_version,
        "status": "running",
        "docs": "/api/v1/docs",
        "redoc": "/api/v1/redoc"
    }

# Healthcheck
@app.get("/api/v1/health", tags=["health"])
async def api_health_check():
    # Проверяем статус ML моделей
    ml_status = "loaded" if get_pipeline() is not None else "fallback"
    
    return {
        "status": "healthy",
        "version": settings.app_version,
        "database": "connected",
        "ml_models": ml_status,
        "api": "v1"
    }

# Info endpoint
@app.get("/api/v1/info", tags=["info"])
async def api_info():
    return {
        "api_version": "v1",
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "endpoints": {
            "products": "/api/v1/products",
            "reviews": "/api/v1/reviews",
            "analytics": "/api/v1/analytics",
            "predict": "/api/v1/predict",
            "aspects": "/api/v1/aspects"
        }
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

