# 🚀 Backend - FastAPI сервис для анализа отзывов

## 🎯 Обзор

Backend представляет собой высокопроизводительный REST API на базе FastAPI, который обеспечивает интеграцию ML моделей, управление данными и аналитические возможности для дашборда анализа отзывов Газпромбанка.

## 🏗️ Архитектура системы

### Технологический стек
- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL / SQLite
- **ORM**: SQLAlchemy 2.0+
- **Validation**: Pydantic v2
- **ML Integration**: TF-IDF + XLM-RoBERTa
- **Server**: Uvicorn ASGI
- **Authentication**: JWT (планируется)

### Структура проекта
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Главное FastAPI приложение
│   ├── config.py              # Конфигурация и настройки
│   ├── database.py            # Подключение к БД
│   ├── models.py              # SQLAlchemy модели
│   ├── schemas.py             # Pydantic схемы
│   ├── crud.py                # CRUD операции
│   ├── ml/                    # ML интеграция
│   │   ├── pipeline.py        # Основной ML пайплайн
│   │   ├── tfidf_model.py     # TF-IDF классификатор
│   │   ├── xlmr_model.py      # XLM-RoBERTa модель
│   │   ├── xlmr_postprocess.py # Постобработка
│   │   └── utils.py           # ML утилиты
│   ├── routers/               # API роутеры
│   │   ├── analytics.py       # Аналитические эндпоинты
│   │   ├── aspects.py         # Аспектный анализ
│   │   ├── predict.py         # ML предсказания
│   │   ├── products.py        # Управление продуктами
│   │   └── reviews.py         # Управление отзывами
│   └── utils/                 # Утилиты
│       ├── etl_loader.py      # ETL загрузка данных
│       └── stats_builder.py   # Построение статистики
├── Dockerfile                 # Docker контейнер
├── requirements.txt           # Python зависимости
├── run_etl.py                # ETL скрипт
├── run_server.py             # Запуск сервера
└── README.md                 # Документация
```

## 🔧 Конфигурация и настройки

### Класс Settings
```python
class Settings(BaseSettings):
    """Настройки приложения"""
    
    # База данных
    database_url: str = "postgresql://postgres:postgres@localhost:5432/gazprombank_reviews"
    
    # FastAPI
    app_name: str = "Gazprombank Reviews Dashboard API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # CORS - динамические настройки по окружению
    environment: str = "development"  # development, staging, production
    
    @property
    def allowed_origins(self) -> list:
        """Динамические CORS origins"""
        if self.environment == "development":
            return [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
                "null"
            ]
        elif self.environment == "production":
            return [
                "https://gazprombank-dashboard.vercel.app",
                "https://gazprombank-dashboard.herokuapp.com"
            ]
    
    # Пагинация
    default_page_size: int = 50
    max_page_size: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### Переменные окружения
```bash
# .env файл
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gazprombank_reviews
DEBUG=True
ENVIRONMENT=development
ADDITIONAL_CORS_ORIGINS=https://custom-domain.com
```

## 📊 Модели данных

### SQLAlchemy модели
```python
class Product(Base):
    """Модель продукта/услуги банка"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    reviews = relationship("Review", back_populates="product")

class Review(Base):
    """Модель отзыва клиента"""
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(String(50), unique=True, index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    review_text = Column(Text, nullable=False)
    review_date = Column(DateTime, nullable=False, index=True)
    url = Column(String(500))
    parsed_at = Column(DateTime, nullable=False)
    bank_name = Column(String(50), nullable=False)
    rating = Column(Integer, nullable=False)
    tonality = Column(String(20), nullable=False, index=True)
    validation = Column(String(100))
    is_valid = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    product = relationship("Product", back_populates="reviews")

class ReviewStats(Base):
    """Предварительно агрегированная статистика"""
    __tablename__ = "review_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    tonality = Column(String(20), nullable=False, index=True)
    count = Column(Integer, nullable=False, default=0)
    avg_rating = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Pydantic схемы
```python
class FileUploadItem(BaseModel):
    """Элемент загружаемого файла"""
    id: Union[int, str] = Field(..., description="ID отзыва")
    text: str = Field(..., min_length=1, description="Текст отзыва")

class FileUploadData(BaseModel):
    """Структура загружаемого JSON файла"""
    data: List[FileUploadItem] = Field(..., min_items=1, description="Список отзывов")

class PredictResponse(BaseModel):
    """Ответ API предсказания"""
    success: bool = Field(..., description="Статус успеха")
    message: str = Field(..., description="Сообщение")
    total_items: int = Field(..., description="Общее количество элементов")
    data: List[Dict[str, Any]] = Field(..., description="Результаты предсказания")

class ErrorResponse(BaseModel):
    """Схема ошибки API"""
    message: str = Field(..., description="Сообщение об ошибке")
    error_code: str = Field(..., description="Код ошибки")
    details: Optional[Dict[str, Any]] = Field(None, description="Детали ошибки")
```

## 🛣️ API Роутеры и эндпоинты

### 1. Products Router (`/api/v1/products`)

```python
@router.get("/", response_model=List[Product])
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Получить список всех продуктов"""

@router.get("/stats", response_model=List[ProductTonalityStats])
async def get_products_with_stats(
    db: Session = Depends(get_db)
):
    """Получить продукты с статистикой по тональности"""

@router.get("/{product_id}", response_model=Product)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Получить продукт по ID"""
```

### 2. Reviews Router (`/api/v1/reviews`)

```python
@router.get("/", response_model=List[Review])
async def get_reviews(
    product_ids: Optional[List[int]] = Query(None),
    tonality: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    max_rating: Optional[int] = Query(None, ge=1, le=5),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Получить отзывы с фильтрацией"""

@router.get("/count")
async def get_reviews_count(
    product_ids: Optional[List[int]] = Query(None),
    tonality: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Получить количество отзывов"""
```

### 3. Analytics Router (`/api/v1/analytics`)

```python
@router.get("/summary")
async def get_analytics_summary(
    product_ids: Optional[List[int]] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Общая сводка аналитики"""

@router.get("/tonality")
async def get_tonality_distribution(
    product_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db)
):
    """Распределение по тональности"""

@router.get("/dynamics")
async def get_tonality_dynamics(
    interval: str = Query("month", regex="^(day|week|month)$"),
    product_ids: Optional[List[int]] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Динамика тональности по времени"""
```

### 4. Predict Router (`/api/v1/predict`)

```python
@router.post("/", response_model=PredictResponse)
async def predict_file(file: UploadFile = File(...)):
    """
    Обработка загруженного JSON файла для предсказания тональности
    
    Принимает JSON файл в формате:
    {
        "data": [
            {"id": 1, "text": "Отзыв о банке..."},
            {"id": 2, "text": "Еще один отзыв..."}
        ]
    }
    
    Возвращает результат ML анализа с тональностью и продуктами
    """

@router.get("/health")
async def predict_health():
    """Проверка здоровья ML пайплайна"""
```

## 🤖 ML интеграция

### InferencePipeline класс
```python
class InferencePipeline:
    def __init__(self, tfidf_path: str, xlmr_path: str):
        """Инициализация ML пайплайна"""
        self.tfidf_model = TfidfClassifier(tfidf_path)
        self.xlmr_tokenizer, self.xlmr_model, self.xlmr_config = load_pretrained(xlmr_path)
        
    def run_from_json(self, json_data: List[Dict]) -> pd.DataFrame:
        """Поклаузные предсказания из JSON"""
        
    def run_and_aggregate_from_json(self, json_data: List[Dict]) -> pd.DataFrame:
        """Агрегированные предсказания по отзывам"""
```

### ML Pipeline инициализация
```python
# Глобальная инициализация ML пайплайна при старте сервера
try:
    logger.info("Инициализация ML пайплайна...")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    tfidf_model_path = os.path.join(project_root, "models/tfidf_lr/model.pkl")
    xlmr_model_path = os.path.join(project_root, "models/xlmr")
    
    ml_pipeline = InferencePipeline(
        tfidf_path=tfidf_model_path,
        xlmr_path=xlmr_model_path
    )
    logger.info("✅ ML пайплайн успешно инициализирован")
except Exception as e:
    logger.error(f"❌ Ошибка инициализации ML пайплайна: {e}")
    ml_pipeline = None
```

### Обработка ML запросов
```python
# Проверка доступности ML пайплайна
if ml_pipeline is None:
    logger.warning("ML пайплайн недоступен, используется заглушка")
    # Fallback логика
else:
    # Подготовка данных для ML
    input_data = [{"id": item.id, "text": item.text} for item in validated_data.data]
    
    # Запуск ML пайплайна
    df_results = ml_pipeline.run_and_aggregate_from_json(input_data)
    
    # Обработка результатов
    processed_items = []
    for review_id in df_results['review_id'].unique():
        review_data = df_results[df_results['review_id'] == review_id].iloc[0]
        
        # Извлечение BERT предсказаний (тональность)
        bert_predictions = review_data.get('pred_agg', {})
        predicted_sentiment = max(set(bert_predictions.values()), 
                                key=list(bert_predictions.values()).count)
        
        # Извлечение TF-IDF предсказаний (продукты)
        tfidf_predictions = review_data.get('pred_tfidf_agg', [])
        
        processed_item = {
            "id": int(review_id),
            "text": str(original_text),
            "predicted_sentiment": str(predicted_sentiment),
            "confidence": float(round(confidence, 3)),
            "predicted_products": [str(p) for p in predicted_products[:5]],
            "bert_details": {str(k): str(v) for k, v in bert_predictions.items()},
            "tfidf_products": [str(p) for p in tfidf_predictions]
        }
        processed_items.append(processed_item)
```

## 🗄️ ETL система

### ETL Loader класс
```python
class ETLLoader:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.stats = {
            "products_created": 0,
            "reviews_loaded": 0,
            "reviews_skipped": 0,
            "errors": 0
        }
    
    def load_json_file(self, file_path: str) -> None:
        """Загрузка данных из JSON файла"""
        
    def create_or_get_product(self, product_name: str) -> Product:
        """Создание или получение продукта"""
        
    def process_review_data(self, review_data: dict, product: Product) -> None:
        """Обработка данных отзыва"""
```

### Запуск ETL
```bash
# Полная загрузка данных
python run_etl.py

# С параметрами
python run_etl.py --data-path /path/to/data --skip-stats

# Только статистика
python run_etl.py --skip-load
```

### ETL логирование
```
2025-09-27 15:30:00 - INFO - Начало ETL процесса
2025-09-27 15:30:01 - INFO - Загрузка данных из: data/raw/banki_ru/
2025-09-27 15:30:02 - INFO - Создан новый продукт: Дебетовые карты
2025-09-27 15:30:05 - INFO - Загружено 15534 отзывов из debitcards.json
2025-09-27 15:30:30 - INFO - ИТОГОВАЯ СТАТИСТИКА:
2025-09-27 15:30:30 - INFO - Продуктов создано: 13
2025-09-27 15:30:30 - INFO - Отзывов загружено: 31921
2025-09-27 15:30:30 - INFO - Отзывов пропущено: 0
2025-09-27 15:30:30 - INFO - Ошибок: 0
```

## 🔒 Безопасность и валидация

### Валидация входных данных
```python
# Проверка типа файла
if not file.content_type or "json" not in file.content_type.lower():
    raise HTTPException(status_code=400, detail="Поддерживаются только JSON файлы")

# Проверка размера файла (10MB лимит)
if file.size and file.size > 10 * 1024 * 1024:
    raise HTTPException(status_code=400, detail="Файл слишком большой")

# Валидация JSON структуры
try:
    validated_data = FileUploadData.parse_obj(json_data)
except ValidationError as e:
    raise HTTPException(status_code=422, detail=f"Ошибка валидации: {e}")
```

### CORS настройки
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # Динамические origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### Обработка ошибок
```python
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
```

## 📊 Производительность и оптимизация

### Метрики производительности
- **Время отклика API**: <100ms для простых запросов
- **ML обработка**: ~200ms на отзыв
- **Пропускная способность**: 300+ запросов/минуту
- **Использование памяти**: ~4GB (с загруженными ML моделями)

### Оптимизации базы данных
```python
# Индексы для быстрых запросов
class Review(Base):
    review_id = Column(String(50), unique=True, index=True)  # Уникальность
    product_id = Column(Integer, ForeignKey("products.id"), index=True)  # Фильтрация
    review_date = Column(DateTime, index=True)  # Временные фильтры
    tonality = Column(String(20), index=True)  # Фильтрация по тональности
    is_valid = Column(Boolean, default=True, index=True)  # Валидные отзывы

# Предварительно агрегированная статистика
class ReviewStats(Base):
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    date = Column(Date, index=True)
    tonality = Column(String(20), index=True)
```

### Кэширование
```python
# Планируется Redis кэширование для:
# - Статистики по продуктам
# - Результатов аналитики
# - ML предсказаний

@lru_cache(maxsize=128)
def get_product_stats_cached(product_id: int) -> Dict:
    """Кэшированная статистика продукта"""
    pass
```

## 🚀 Развертывание

### Docker контейнер
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY app/ ./app/
COPY models/ ./models/

# Переменные окружения
ENV PYTHONPATH=/app
ENV DATABASE_URL=postgresql://postgres:postgres@db:5432/gazprombank_reviews

# Запуск
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/gazprombank_reviews
    depends_on:
      - db
    volumes:
      - ./models:/app/models

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: gazprombank_reviews
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Запуск в production
```bash
# Через Docker Compose
docker-compose up -d

# Через Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Через Gunicorn + Uvicorn workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📈 Мониторинг и логирование

### Система логирования
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# Специализированные логгеры
logger = logging.getLogger(__name__)
ml_logger = logging.getLogger("ml_pipeline")
etl_logger = logging.getLogger("etl")
```

### Health Check эндпоинты
```python
@app.get("/health")
async def health_check():
    """Базовая проверка здоровья"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "database": "connected",
        "ml_pipeline": "available" if ml_pipeline else "unavailable"
    }

@app.get("/api/v1/predict/health")
async def predict_health():
    """Проверка ML пайплайна"""
    if ml_pipeline is None:
        raise HTTPException(status_code=503, detail="ML пайплайн недоступен")
    
    return {
        "status": "healthy",
        "ml_pipeline": "ready",
        "models": {
            "tfidf": "loaded",
            "xlmr": "loaded"
        }
    }
```

### Метрики для мониторинга
```python
# Планируемые метрики (Prometheus/Grafana)
metrics = {
    "api_requests_total": "Общее количество API запросов",
    "api_request_duration_seconds": "Время обработки запросов",
    "ml_predictions_total": "Количество ML предсказаний",
    "ml_prediction_duration_seconds": "Время ML обработки",
    "database_connections_active": "Активные подключения к БД",
    "memory_usage_bytes": "Использование памяти",
    "cpu_usage_percent": "Использование CPU"
}
```

## 🧪 Тестирование

### Unit тесты
```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_products():
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_predict_endpoint():
    test_data = {
        "data": [
            {"id": 1, "text": "Отличный банк!"}
        ]
    }
    response = client.post("/api/v1/predict/", json=test_data)
    assert response.status_code == 200
```

### Интеграционные тесты
```bash
# Тестирование всех эндпоинтов
python test_api_integration.py

# Нагрузочное тестирование
locust -f load_test.py --host=http://localhost:8000
```

## 📚 API документация

### Автоматическая документация
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Примеры использования API
```python
import requests

# Получение продуктов с статистикой
response = requests.get("http://localhost:8000/api/v1/products/stats")
products = response.json()

# Анализ тональности файла
files = {"file": open("reviews.json", "rb")}
response = requests.post("http://localhost:8000/api/v1/predict/", files=files)
results = response.json()

# Аналитика по тональности
params = {"product_ids": [1, 2], "start_date": "2024-01-01"}
response = requests.get("http://localhost:8000/api/v1/analytics/tonality", params=params)
analytics = response.json()
```

## 🔧 Настройка разработки

### Установка зависимостей
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Запуск в режиме разработки
```bash
# Через скрипт
python run_server.py

# Через uvicorn с автоперезагрузкой
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Через FastAPI CLI
fastapi dev app/main.py
```

### Форматирование и линтинг
```bash
# Форматирование кода
black app/
isort app/

# Проверка качества кода
flake8 app/
mypy app/

# Тестирование
pytest tests/
```

## 🔗 Связанные разделы

- [04-classification.md](04-classification.md) - ML модели, интегрированные в API
- [06-frontend.md](06-frontend.md) - Frontend, использующий Backend API
- [03-data-labeling.md](03-data-labeling.md) - Данные, загружаемые через ETL
- [07-architecture.md](07-architecture.md) - Общая архитектура системы

---

*Документация создана для проекта анализа тональности отзывов Газпромбанка*
