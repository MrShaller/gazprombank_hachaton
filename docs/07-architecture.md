# 🏛️ Архитектура системы - Полный обзор

## 🎯 Обзор системы

Система анализа тональности отзывов Газпромбанка представляет собой комплексное решение, включающее сбор данных, машинное обучение, backend API и современный веб-интерфейс. Архитектура построена по принципам микросервисов с четким разделением ответственности между компонентами.

## 🏗️ Высокоуровневая архитектура

```mermaid
graph TB
    subgraph "Data Sources"
        A[Sravni.ru] 
        B[Banki.ru]
    end
    
    subgraph "Data Processing Pipeline"
        C[Web Scrapers] --> D[Raw Data Storage]
        D --> E[Data Preprocessing]
        E --> F[Clustering & Analysis]
        F --> G[Data Labeling]
        G --> H[ML Training]
    end
    
    subgraph "ML Models"
        I[TF-IDF + LR]
        J[XLM-RoBERTa]
        H --> I
        H --> J
    end
    
    subgraph "Production System"
        K[PostgreSQL DB]
        L[FastAPI Backend]
        M[Next.js Frontend]
        N[ML Pipeline]
    end
    
    subgraph "Infrastructure"
        O[Docker Containers]
        P[Load Balancer]
        Q[Monitoring]
    end
    
    A --> C
    B --> C
    D --> K
    I --> N
    J --> N
    N --> L
    L --> M
    L --> K
    
    O --> L
    O --> M
    O --> K
    P --> O
    Q --> O
    
    style A fill:#e1f5fe
    style B fill:#e1f5fe
    style I fill:#f3e5f5
    style J fill:#f3e5f5
    style L fill:#e8f5e8
    style M fill:#fff3e0
    style K fill:#fce4ec
```

## 📊 Компонентная архитектура

### 1. Data Layer (Слой данных)
```mermaid
graph LR
    subgraph "Raw Data"
        A[Sravni.ru JSON]
        B[Banki.ru JSON]
        C[Merged Reviews]
    end
    
    subgraph "Processed Data"
        D[Clauses CSV]
        E[Labeled Data]
        F[ML Features]
    end
    
    subgraph "Production DB"
        G[Products Table]
        H[Reviews Table]
        I[Review Stats]
    end
    
    A --> C
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    F --> H
    H --> I
```

**Характеристики:**
- **Объем данных**: 58,000+ отзывов
- **Формат хранения**: JSON → CSV → PostgreSQL
- **Обновление**: Batch processing
- **Резервное копирование**: Ежедневное

### 2. ML Pipeline (ML конвейер)
```mermaid
graph TD
    A[Raw Review Text] --> B[Text Preprocessing]
    B --> C[Clause Splitting]
    C --> D{ML Pipeline}
    
    D --> E[TF-IDF Classifier]
    D --> F[XLM-RoBERTa Model]
    
    E --> G[Product Classification]
    F --> H[Sentiment Analysis]
    
    G --> I[Results Aggregation]
    H --> I
    I --> J[Final Output]
    
    style E fill:#e3f2fd
    style F fill:#f3e5f5
    style I fill:#e8f5e8
```

**Технические характеристики:**
- **Производительность**: 300 отзывов/минуту
- **Точность**: 85% общая точность
- **Латентность**: ~200ms на отзыв
- **Масштабируемость**: Горизонтальное масштабирование

### 3. Backend Architecture (Архитектура бэкенда)
```mermaid
graph TB
    subgraph "API Layer"
        A[FastAPI Router]
        B[Authentication Middleware]
        C[CORS Middleware]
        D[Error Handler]
    end
    
    subgraph "Business Logic"
        E[Products Service]
        F[Reviews Service]
        G[Analytics Service]
        H[ML Service]
    end
    
    subgraph "Data Access"
        I[SQLAlchemy ORM]
        J[Database Models]
        K[CRUD Operations]
    end
    
    subgraph "External Services"
        L[ML Pipeline]
        M[File Storage]
        N[Logging Service]
    end
    
    A --> E
    A --> F
    A --> G
    A --> H
    
    E --> I
    F --> I
    G --> I
    H --> L
    
    I --> J
    J --> K
    
    style A fill:#e3f2fd
    style L fill:#f3e5f5
    style I fill:#e8f5e8
```

**Технологический стек:**
- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 14+
- **ORM**: SQLAlchemy 2.0+
- **Validation**: Pydantic v2
- **Authentication**: JWT (планируется)

### 4. Frontend Architecture (Архитектура фронтенда)
```mermaid
graph TB
    subgraph "Presentation Layer"
        A[Next.js Pages]
        B[React Components]
        C[Tailwind Styles]
    end
    
    subgraph "State Management"
        D[Custom Hooks]
        E[Context API]
        F[Local State]
    end
    
    subgraph "Data Layer"
        G[API Client]
        H[Type Definitions]
        I[Error Handling]
    end
    
    subgraph "UI Components"
        J[Charts - Recharts]
        K[Forms - React Hook Form]
        L[Modals - Custom]
        M[Filters - Custom]
    end
    
    A --> B
    B --> D
    D --> G
    
    B --> J
    B --> K
    B --> L
    B --> M
    
    G --> H
    G --> I
    
    style A fill:#fff3e0
    style G fill:#e3f2fd
    style J fill:#f3e5f5
```

**Технологический стек:**
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5.9+
- **Styling**: Tailwind CSS 3.3+
- **Charts**: Recharts 2.15+
- **HTTP**: Axios 1.6+

## 🔄 Потоки данных

### 1. ETL Pipeline (Конвейер ETL)
```mermaid
sequenceDiagram
    participant S as Web Scrapers
    participant R as Raw Storage
    participant P as Preprocessor
    participant C as Clustering
    participant L as Labeling
    participant M as ML Training
    participant D as Production DB
    
    S->>R: Store raw reviews
    R->>P: Load and clean data
    P->>C: Cluster similar reviews
    C->>L: Generate training data
    L->>M: Train ML models
    M->>D: Deploy to production
    
    Note over S,D: Offline batch processing
```

### 2. Real-time Prediction Flow (Поток предсказаний в реальном времени)
```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend API
    participant ML as ML Pipeline
    participant DB as Database
    
    U->>F: Upload JSON file
    F->>B: POST /api/v1/predict/
    B->>ML: Process reviews
    ML->>ML: TF-IDF classification
    ML->>ML: XLM-RoBERTa sentiment
    ML->>B: Return results
    B->>F: JSON response
    F->>U: Download processed file
    
    Note over U,DB: Real-time processing
```

### 3. Analytics Data Flow (Поток аналитических данных)
```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend API
    participant DB as Database
    participant C as Cache
    
    U->>F: Select filters
    F->>B: GET /api/v1/analytics/
    B->>C: Check cache
    alt Cache hit
        C->>B: Return cached data
    else Cache miss
        B->>DB: Query database
        DB->>B: Return results
        B->>C: Store in cache
    end
    B->>F: JSON response
    F->>U: Update charts
    
    Note over U,C: Cached analytics
```

## 🐳 Deployment Architecture (Архитектура развертывания)

### Docker Compose Setup
```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: gazprombank_reviews
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 10s
      retries: 5

  # FastAPI Backend
  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/gazprombank_reviews
      DEBUG: "false"
    volumes:
      - ./models:/app/models:ro
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Next.js Frontend
  frontend:
    build: ./frontend
    environment:
      NEXT_PUBLIC_API_URL: http://backend:8000/api/v1
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 5

networks:
  gazprombank_network:
    driver: bridge

volumes:
  postgres_data:
```

### Production Deployment Diagram
```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Nginx/Traefik]
    end
    
    subgraph "Frontend Tier"
        F1[Frontend Instance 1]
        F2[Frontend Instance 2]
    end
    
    subgraph "Backend Tier"
        B1[Backend Instance 1]
        B2[Backend Instance 2]
        B3[Backend Instance 3]
    end
    
    subgraph "Data Tier"
        DB[(PostgreSQL Primary)]
        DBR[(PostgreSQL Replica)]
        REDIS[(Redis Cache)]
    end
    
    subgraph "ML Tier"
        ML1[ML Pipeline 1]
        ML2[ML Pipeline 2]
    end
    
    subgraph "Monitoring"
        PROM[Prometheus]
        GRAF[Grafana]
        LOG[Loki/ELK]
    end
    
    LB --> F1
    LB --> F2
    
    F1 --> B1
    F1 --> B2
    F2 --> B2
    F2 --> B3
    
    B1 --> DB
    B2 --> DB
    B3 --> DB
    
    B1 --> REDIS
    B2 --> REDIS
    B3 --> REDIS
    
    B1 --> ML1
    B2 --> ML1
    B3 --> ML2
    
    DB --> DBR
    
    B1 --> PROM
    B2 --> PROM
    B3 --> PROM
    PROM --> GRAF
    
    style LB fill:#e3f2fd
    style DB fill:#fce4ec
    style REDIS fill:#fff3e0
    style ML1 fill:#f3e5f5
    style ML2 fill:#f3e5f5
```

## 📁 Структура проекта

```
gazprombank_hachaton/
├── 📊 data/                          # Данные и результаты
│   ├── raw/                          # Исходные данные
│   │   ├── banki_ru/                 # Данные с Banki.ru
│   │   └── sravni_ru/                # Данные с Sravni.ru
│   ├── interim/                      # Промежуточные данные
│   └── processed/                    # Обработанные данные
│       ├── clustering/               # Результаты кластеризации
│       └── labeling/                 # Размеченные данные
│
├── 🤖 models/                        # Обученные ML модели
│   ├── tfidf_lr/                     # TF-IDF + Logistic Regression
│   └── xlmr/                         # XLM-RoBERTa модель
│
├── 📜 scripts/                       # Скрипты обработки данных
│   ├── parsers/                      # Парсеры веб-сайтов
│   ├── clustering/                   # Кластеризация данных
│   ├── labeling/                     # Разметка данных
│   ├── models/                       # Обучение ML моделей
│   └── sentiments/                   # Анализ тональности
│
├── 🚀 backend/                       # FastAPI backend
│   ├── app/                          # Основное приложение
│   │   ├── ml/                       # ML интеграция
│   │   ├── routers/                  # API роутеры
│   │   └── utils/                    # Утилиты
│   ├── Dockerfile                    # Docker образ
│   └── requirements.txt              # Python зависимости
│
├── 🎨 frontend/                      # Next.js frontend
│   ├── src/                          # Исходный код
│   │   ├── app/                      # Next.js App Router
│   │   ├── components/               # React компоненты
│   │   ├── hooks/                    # Custom hooks
│   │   ├── lib/                      # Утилиты и API
│   │   └── types/                    # TypeScript типы
│   ├── public/                       # Статические файлы
│   ├── Dockerfile                    # Docker образ
│   └── package.json                  # Node.js зависимости
│
├── 📚 docs/                          # Документация
│   ├── 01-data-collection.md         # Сбор данных
│   ├── 02-clustering.md              # Кластеризация
│   ├── 03-data-labeling.md           # Разметка данных
│   ├── 04-classification.md          # ML классификация
│   ├── 05-backend.md                 # Backend API
│   ├── 06-frontend.md                # Frontend приложение
│   └── 07-architecture.md            # Архитектура системы
│
├── 📊 reports/                       # Отчеты и визуализации
│   ├── clustering/                   # Результаты кластеризации
│   └── labeling/                     # Статистика разметки
│
├── ⚙️ configs/                       # Конфигурационные файлы
├── 🧪 tests/                         # Тесты
├── 🐳 docker-compose.yml             # Docker Compose
├── 🚀 DEPLOYMENT.md                  # Инструкции по развертыванию
└── 📖 README.md                      # Основная документация
```

## 🔧 Технологический стек

### Backend Stack
| Компонент | Технология | Версия | Назначение |
|-----------|------------|--------|------------|
| **Web Framework** | FastAPI | 0.104+ | REST API сервер |
| **Database** | PostgreSQL | 14+ | Основная БД |
| **ORM** | SQLAlchemy | 2.0+ | Работа с БД |
| **Validation** | Pydantic | v2 | Валидация данных |
| **ML Framework** | scikit-learn | 1.3+ | TF-IDF модель |
| **DL Framework** | PyTorch | 2.0+ | XLM-RoBERTa модель |
| **NLP Library** | Transformers | 4.30+ | Предобученные модели |
| **Server** | Uvicorn | - | ASGI сервер |

### Frontend Stack
| Компонент | Технология | Версия | Назначение |
|-----------|------------|--------|------------|
| **Framework** | Next.js | 14+ | React фреймворк |
| **Language** | TypeScript | 5.9+ | Типизированный JS |
| **Styling** | Tailwind CSS | 3.3+ | Utility-first CSS |
| **Charts** | Recharts | 2.15+ | Графики и диаграммы |
| **HTTP Client** | Axios | 1.6+ | API запросы |
| **Icons** | Lucide React | 0.294+ | Иконки |
| **Date Handling** | date-fns | 2.30+ | Работа с датами |

### ML/Data Stack
| Компонент | Технология | Версия | Назначение |
|-----------|------------|--------|------------|
| **Data Processing** | Pandas | 2.0+ | Обработка данных |
| **Clustering** | scikit-learn | 1.3+ | Кластеризация |
| **Topic Modeling** | Gensim | 4.3+ | LDA моделирование |
| **Web Scraping** | BeautifulSoup | 4.12+ | Парсинг HTML |
| **Browser Automation** | Selenium | 4.15+ | Автоматизация браузера |
| **Text Processing** | NLTK | 3.8+ | Обработка текста |
| **Russian NLP** | pymorphy3 | 2.0+ | Морфологический анализ |

### Infrastructure Stack
| Компонент | Технология | Версия | Назначение |
|-----------|------------|--------|------------|
| **Containerization** | Docker | 24+ | Контейнеризация |
| **Orchestration** | Docker Compose | v2 | Локальная оркестрация |
| **Database** | PostgreSQL | 14+ | Реляционная БД |
| **Caching** | Redis | 7+ | Кэширование (планируется) |
| **Monitoring** | Prometheus | - | Метрики (планируется) |
| **Logging** | Grafana | - | Визуализация (планируется) |

## 🔄 CI/CD Pipeline

### Development Workflow
```mermaid
graph LR
    A[Local Development] --> B[Git Commit]
    B --> C[GitHub Push]
    C --> D[GitHub Actions]
    D --> E[Tests & Linting]
    E --> F[Build Docker Images]
    F --> G[Deploy to Staging]
    G --> H[Integration Tests]
    H --> I[Deploy to Production]
    
    style D fill:#e3f2fd
    style I fill:#e8f5e8
```

### GitHub Actions Workflow
```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest tests/
      - name: Lint code
        run: |
          cd backend
          flake8 app/
          black --check app/

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests
        run: |
          cd frontend
          npm run test
      - name: Lint code
        run: |
          cd frontend
          npm run lint
      - name: Type check
        run: |
          cd frontend
          npm run type-check

  build-and-deploy:
    needs: [test-backend, test-frontend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker images
        run: |
          docker build -t gazprombank-backend ./backend
          docker build -t gazprombank-frontend ./frontend
      - name: Deploy to production
        run: |
          # Deployment commands
          echo "Deploying to production..."
```

## 📊 Производительность и масштабирование

### Метрики производительности
| Компонент | Метрика | Значение | Цель |
|-----------|---------|----------|------|
| **Backend API** | Response Time | <100ms | <50ms |
| **ML Pipeline** | Processing Time | ~200ms/отзыв | <150ms/отзыв |
| **Database** | Query Time | <50ms | <25ms |
| **Frontend** | First Contentful Paint | <1.8s | <1.5s |
| **Frontend** | Time to Interactive | <3.8s | <3.0s |
| **System** | Throughput | 300 отз/мин | 500 отз/мин |

### Стратегии масштабирования

#### Горизонтальное масштабирование
```mermaid
graph TB
    subgraph "Load Balancer"
        LB[HAProxy/Nginx]
    end
    
    subgraph "Backend Instances"
        B1[Backend 1]
        B2[Backend 2]
        B3[Backend N]
    end
    
    subgraph "ML Workers"
        ML1[ML Worker 1]
        ML2[ML Worker 2]
        ML3[ML Worker N]
    end
    
    subgraph "Database Cluster"
        DBM[(Primary)]
        DBS1[(Replica 1)]
        DBS2[(Replica N)]
    end
    
    LB --> B1
    LB --> B2
    LB --> B3
    
    B1 --> ML1
    B2 --> ML2
    B3 --> ML3
    
    B1 --> DBM
    B2 --> DBS1
    B3 --> DBS2
    
    DBM --> DBS1
    DBM --> DBS2
```

#### Кэширование
```mermaid
graph LR
    A[Client Request] --> B[API Gateway]
    B --> C{Cache Check}
    C -->|Hit| D[Return Cached Data]
    C -->|Miss| E[Process Request]
    E --> F[Update Cache]
    F --> G[Return Data]
    
    style C fill:#fff3e0
    style D fill:#e8f5e8
    style F fill:#e3f2fd
```

**Стратегии кэширования:**
- **API Response Cache**: Redis для аналитических запросов
- **ML Model Cache**: In-memory кэш для загруженных моделей
- **Database Query Cache**: PostgreSQL query cache
- **Static Asset Cache**: CDN для фронтенда

## 🔒 Безопасность

### Архитектура безопасности
```mermaid
graph TB
    subgraph "External"
        U[Users]
        A[Attackers]
    end
    
    subgraph "Security Layer"
        WAF[Web Application Firewall]
        LB[Load Balancer + SSL]
        AUTH[Authentication Service]
    end
    
    subgraph "Application Layer"
        FE[Frontend - HTTPS Only]
        BE[Backend - JWT Auth]
        DB[(Database - Encrypted)]
    end
    
    subgraph "Infrastructure"
        VPC[Private Network]
        FW[Firewall Rules]
        LOG[Security Logging]
    end
    
    U --> WAF
    A --> WAF
    WAF --> LB
    LB --> AUTH
    AUTH --> FE
    FE --> BE
    BE --> DB
    
    VPC --> FE
    VPC --> BE
    VPC --> DB
    FW --> VPC
    LOG --> VPC
    
    style WAF fill:#ffebee
    style AUTH fill:#e8f5e8
    style DB fill:#fce4ec
```

### Меры безопасности

#### 1. Аутентификация и авторизация
```python
# Планируемая JWT аутентификация
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/v1/protected")
async def protected_route(current_user: str = Depends(get_current_user)):
    return {"user": current_user}
```

#### 2. Валидация входных данных
```python
# Строгая валидация с Pydantic
from pydantic import BaseModel, Field, validator
from typing import List

class FileUploadData(BaseModel):
    data: List[Dict[str, Any]] = Field(..., min_items=1, max_items=10000)
    
    @validator('data')
    def validate_data_structure(cls, v):
        for item in v:
            if 'id' not in item or 'text' not in item:
                raise ValueError('Each item must have id and text fields')
            if len(item['text']) > 10000:
                raise ValueError('Text too long')
        return v
```

#### 3. CORS и безопасность заголовков
```python
# Настройка безопасности
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["gazprombank.com", "*.gazprombank.com"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Безопасные заголовки
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

## 📈 Мониторинг и логирование

### Архитектура мониторинга
```mermaid
graph TB
    subgraph "Applications"
        FE[Frontend]
        BE[Backend]
        DB[(Database)]
    end
    
    subgraph "Metrics Collection"
        PROM[Prometheus]
        GRAF[Grafana]
        ALERT[AlertManager]
    end
    
    subgraph "Logging"
        LOG[Application Logs]
        ELK[ELK Stack]
        LOKI[Loki]
    end
    
    subgraph "Monitoring"
        UP[Uptime Monitoring]
        APM[Application Performance]
        ERR[Error Tracking]
    end
    
    FE --> PROM
    BE --> PROM
    DB --> PROM
    
    PROM --> GRAF
    PROM --> ALERT
    
    FE --> LOG
    BE --> LOG
    LOG --> ELK
    LOG --> LOKI
    
    GRAF --> UP
    GRAF --> APM
    ALERT --> ERR
    
    style PROM fill:#e3f2fd
    style GRAF fill:#e8f5e8
    style ELK fill:#fff3e0
```

### Ключевые метрики

#### Backend метрики
```python
# Prometheus метрики для FastAPI
from prometheus_client import Counter, Histogram, Gauge
import time

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active database connections')

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    REQUEST_COUNT.labels(
        method=request.method, 
        endpoint=request.url.path
    ).inc()
    
    REQUEST_LATENCY.observe(time.time() - start_time)
    
    return response
```

#### ML Pipeline метрики
```python
# Метрики для ML пайплайна
ML_PREDICTIONS_TOTAL = Counter('ml_predictions_total', 'Total ML predictions')
ML_PREDICTION_LATENCY = Histogram('ml_prediction_duration_seconds', 'ML prediction latency')
ML_MODEL_ACCURACY = Gauge('ml_model_accuracy', 'Current model accuracy')

def track_ml_prediction(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            ML_PREDICTIONS_TOTAL.inc()
            ML_PREDICTION_LATENCY.observe(time.time() - start_time)
            return result
        except Exception as e:
            ML_PREDICTIONS_TOTAL.labels(status='error').inc()
            raise
    return wrapper
```

### Логирование
```python
# Структурированное логирование
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        
    def log_api_request(self, request, response, duration):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "api_request",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration * 1000,
            "user_agent": request.headers.get("user-agent"),
            "ip": request.client.host
        }
        self.logger.info(json.dumps(log_data))
    
    def log_ml_prediction(self, input_size, output_size, duration, model_type):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "ml_prediction",
            "model_type": model_type,
            "input_size": input_size,
            "output_size": output_size,
            "duration_ms": duration * 1000
        }
        self.logger.info(json.dumps(log_data))
```

## 🚀 Развертывание и DevOps

### Environments (Окружения)
```mermaid
graph LR
    A[Development] --> B[Staging]
    B --> C[Production]
    
    subgraph "Development"
        D1[Local Docker]
        D2[Hot Reload]
        D3[Debug Mode]
    end
    
    subgraph "Staging"
        S1[Cloud Instance]
        S2[Production Data]
        S3[Performance Tests]
    end
    
    subgraph "Production"
        P1[Load Balancer]
        P2[Multiple Instances]
        P3[Monitoring]
    end
    
    A --> D1
    A --> D2
    A --> D3
    
    B --> S1
    B --> S2
    B --> S3
    
    C --> P1
    C --> P2
    C --> P3
```

### Deployment Strategies

#### Blue-Green Deployment
```mermaid
graph TB
    subgraph "Load Balancer"
        LB[HAProxy/Nginx]
    end
    
    subgraph "Blue Environment (Current)"
        B1[Backend v1.0]
        B2[Frontend v1.0]
        BDB[(Database)]
    end
    
    subgraph "Green Environment (New)"
        G1[Backend v1.1]
        G2[Frontend v1.1]
        GDB[(Database)]
    end
    
    LB --> B1
    LB --> B2
    LB -.-> G1
    LB -.-> G2
    
    BDB --> GDB
    
    style B1 fill:#e3f2fd
    style B2 fill:#e3f2fd
    style G1 fill:#e8f5e8
    style G2 fill:#e8f5e8
```

#### Rolling Deployment
```bash
#!/bin/bash
# Rolling deployment script

# 1. Build new images
docker build -t gazprombank-backend:new ./backend
docker build -t gazprombank-frontend:new ./frontend

# 2. Update instances one by one
for instance in backend-1 backend-2 backend-3; do
    echo "Updating $instance..."
    docker stop $instance
    docker rm $instance
    docker run -d --name $instance gazprombank-backend:new
    
    # Health check
    while ! curl -f http://$instance:8000/health; do
        echo "Waiting for $instance to be healthy..."
        sleep 5
    done
    
    echo "$instance updated successfully"
done
```

### Infrastructure as Code
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gazprombank-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gazprombank-backend
  template:
    metadata:
      labels:
        app: gazprombank-backend
    spec:
      containers:
      - name: backend
        image: gazprombank-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## 🔗 Связанные разделы

- [01-data-collection.md](01-data-collection.md) - Сбор и подготовка данных
- [02-clustering.md](02-clustering.md) - Кластеризация и тематическое моделирование
- [03-data-labeling.md](03-data-labeling.md) - Разметка данных с помощью LLM
- [04-classification.md](04-classification.md) - ML модели и классификация
- [05-backend.md](05-backend.md) - FastAPI backend и API
- [06-frontend.md](06-frontend.md) - Next.js frontend и UI/UX

---

*Документация создана для проекта анализа тональности отзывов Газпромбанка*
