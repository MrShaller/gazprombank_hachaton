# 🏦 Газпромбанк | Система анализа тональности отзывов

Комплексная система для автоматического анализа тональности отзывов клиентов банка с использованием машинного обучения и современного веб-интерфейса.

## 🌐 **Живая демонстрация**
**🚀 [Попробовать систему в действии →](http://itsfour-solution.ru/)**

![Дашборд](logo-gazprombank.png)

## 🎯 О проекте

Полнофункциональная система анализа отзывов клиентов Газпромбанка включает:

### 🔄 **Data Pipeline**
- **Сбор данных** с Sravni.ru и Banki.ru (58,000+ отзывов)
- **Кластеризация** и тематическое моделирование (13 категорий)
- **Автоматическая разметка** с помощью LLM Ollama (46,312 клауз)

### 🤖 **Machine Learning**
- **Гибридная ML система** (TF-IDF + XLM-RoBERTa)
- **85% точность** классификации
- **Предзагрузка моделей** при старте backend'а
- **Анализ тональности** по продуктам в реальном времени

### 💻 **Веб-приложение**
- **FastAPI backend** с ML интеграцией
- **Next.js frontend** с интерактивными дашбордами
- **Загрузка файлов** для ML анализа
- **Визуализация данных** через графики и диаграммы

## 🏗️ Структура проекта

```
gazprombank_hachaton/
├── 📊 data/                          # Данные и результаты
│   ├── raw/                          # Исходные данные (58k+ отзывов)
│   ├── interim/                      # Промежуточные данные
│   └── processed/                    # Обработанные данные
├── 🤖 models/                        # Обученные ML модели
│   ├── tfidf_lr/                     # TF-IDF + Logistic Regression
│   └── xlmr/                         # XLM-RoBERTa модель
├── 📜 scripts/                       # Data Science pipeline
│   ├── parsers/                      # Парсеры веб-сайтов
│   ├── clustering/                   # Кластеризация данных
│   ├── labeling/                     # Разметка с Ollama LLM
│   └── models/                       # Обучение ML моделей
├── 🚀 backend/                       # FastAPI backend
│   ├── app/                          # Основное приложение
│   │   ├── ml/                       # ML интеграция
│   │   ├── routers/                  # API роутеры
│   │   └── utils/                    # Утилиты
│   └── requirements.txt              # Python зависимости
├── 🎨 frontend/                      # Next.js frontend
│   ├── src/                          # Исходный код
│   │   ├── app/                      # Next.js App Router
│   │   ├── components/               # React компоненты
│   │   ├── hooks/                    # Custom hooks
│   │   └── lib/                      # API клиент
│   └── package.json                  # Node.js зависимости
├── 📚 docs/                          # Документация
│   ├── 01-data-collection.md         # Сбор данных
│   ├── 02-clustering.md              # Кластеризация
│   ├── 03-data-labeling.md           # Разметка данных
│   ├── 04-classification.md          # ML классификация
│   ├── 05-backend.md                 # Backend API
│   ├── 06-frontend.md                # Frontend приложение
│   └── 07-architecture.md            # Архитектура системы
└── 🐳 docker-compose.yml             # Docker оркестрация
```

## 📚 Документация

### 🔗 **Полная техническая документация**
Детальная документация по всем компонентам системы находится в папке [`docs/`](docs/):

- **[📖 Обзор проекта](docs/README.md)** - Центральный хаб документации
- **[📊 Сбор данных](docs/01-data-collection.md)** - Парсинг 58k+ отзывов
- **[🧠 Кластеризация](docs/02-clustering.md)** - Тематическое моделирование
- **[🏷️ Разметка данных](docs/03-data-labeling.md)** - LLM разметка с Ollama
- **[🤖 ML классификация](docs/04-classification.md)** - Гибридные ML модели
- **[🚀 Backend API](docs/05-backend.md)** - FastAPI с ML интеграцией
- **[🎨 Frontend](docs/06-frontend.md)** - Next.js дашборды
- **[🏛️ Архитектура](docs/07-architecture.md)** - Полный обзор системы

## 🚀 Быстрый старт

### 🐳 **Docker Compose (Рекомендуется)**

```bash
# 1. Клонирование репозитория
git clone <repository-url>
cd gazprombank_hachaton

# 2. Запуск всей системы
docker-compose up --build -d

# 3. Загрузка данных
docker-compose exec backend python run_etl.py

# 4. Доступ к приложению
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### 💻 **Локальная разработка**

#### Предварительные требования
- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 14+**
- **Git**

#### 1️⃣ Клонирование и настройка

```bash
# Клонирование репозитория
git clone <repository-url>
cd gazprombank_hachaton

# Настройка PostgreSQL (macOS)
brew install postgresql@14
brew services start postgresql@14
createuser -s postgres
createdb gazprombank_reviews
```

#### 2️⃣ Backend запуск

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python run_etl.py         # Загрузка данных
python run_server.py      # Запуск сервера
```

#### 3️⃣ Frontend запуск

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev
```

**Результат:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🗄️ База данных

### Структура таблиц

#### `products` - Продукты/услуги
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `reviews` - Отзывы клиентов
```sql
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    review_id VARCHAR(50) UNIQUE NOT NULL,
    product_id INTEGER REFERENCES products(id),
    review_text TEXT NOT NULL,
    review_date TIMESTAMP NOT NULL,
    url VARCHAR(500),
    parsed_at TIMESTAMP NOT NULL,
    bank_name VARCHAR(50) NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    tonality VARCHAR(20) CHECK (tonality IN ('положительно', 'отрицательно', 'нейтрально')),
    validation VARCHAR(100),
    is_valid BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `review_stats` - Агрегированная статистика
```sql
CREATE TABLE review_stats (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    date TIMESTAMP NOT NULL,
    tonality VARCHAR(20) NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    avg_rating INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Пример данных

```json
{
  "review_id": "12345",
  "review_text": "Отличный банк, рекомендую!",
  "review_date": "31.05.2025 14:52",
  "url": "https://www.banki.ru/services/responses/bank/response/12345/",
  "parsed_at": "2025-09-27T15:06:33.492134",
  "bank_name": "gazprombank",
  "product_type": "Ипотека",
  "rating": 5,
  "tonality": "положительно",
  "validation": "Отзыв проверен",
  "is_valid": true
}
```

## 📡 API Эндпоинты

### Продукты
- `GET /api/v1/products` - список всех продуктов
- `GET /api/v1/products/stats` - продукты с детальной статистикой
- `GET /api/v1/products/{id}` - продукт по ID

### Отзывы
- `GET /api/v1/reviews` - список отзывов с фильтрацией
- `GET /api/v1/reviews/count` - количество отзывов
- `GET /api/v1/reviews/{id}` - отзыв по ID

### Аналитика
- `GET /api/v1/analytics/summary` - общая сводная статистика
- `GET /api/v1/analytics/tonality` - распределение по тональностям
- `GET /api/v1/analytics/dynamics` - динамика изменений по времени
- `GET /api/v1/analytics/ratings` - распределение по рейтингам
- `GET /api/v1/analytics/top-reviews` - топ отзывы

### ML Анализ
- `POST /api/v1/predict/` - анализ тональности (возвращает файл с результатами)
- `POST /api/v1/predict/json` - анализ тональности (возвращает JSON ответ)
- `GET /api/v1/predict/health` - проверка работоспособности ML сервиса

### Служебные
- `GET /` - информация об API
- `GET /health` - проверка здоровья сервиса
- `GET /api/v1/health` - проверка здоровья API (включая статус ML моделей)

### Примеры запросов

```bash
# Получить статистику по продуктам
curl http://localhost:8000/api/v1/products/stats

# Проверить статус API и ML моделей
curl http://localhost:8000/api/v1/health

# Получить распределение тональности для продукта
curl "http://localhost:8000/api/v1/analytics/tonality?product_id=1"

# Получить динамику по месяцам
curl "http://localhost:8000/api/v1/analytics/dynamics?interval=month"

# Получить топ положительных отзывов
curl "http://localhost:8000/api/v1/analytics/top-reviews?tonality=положительно&limit=5"

# Анализ тональности - получить файл с результатами (production)
curl -X POST "http://itsfour-solution.ru/api/v1/predict" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@example_reviews.json;type=application/json" \
  -o "results.json"

# Анализ тональности - получить JSON ответ (production)
curl -X POST "http://itsfour-solution.ru/api/v1/predict/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@example_reviews.json;type=application/json"
```

#### Пример входного файла (example_reviews.json):

```json
{
  "data": [
    {
      "id": 1,
      "text": "Отличное мобильное приложение! Но обслуживание в офисе плохое."
    },
    {
      "id": 2,
      "text": "Кредитная карта работает нормально, без проблем."
    }
  ]
}
```

#### Пример результирующего файла (example_reviews_predictions.json):

```json
{
  "predictions": [
    {
      "id": 1,
      "topics": ["Мобильное приложение", "Обслуживание"],
      "sentiments": ["положительно", "отрицательно"]
    },
    {
      "id": 2,
      "topics": ["Кредитная карта"],
      "sentiments": ["нейтрально"]
    },
    {
      "id": 3,
      "topics": ["Обслуживание"],
      "sentiments": ["отрицательно"]
    }
  ]
}
```

#### ❌ Частые ошибки использования:

```bash
# НЕПРАВИЛЬНО - отправка текста в теле запроса
curl -X POST "http://itsfour-solution.ru/api/v1/predict/" \
  -H "Content-Type: application/json" \
  -d '{"data": [{"id": 1, "text": "Отзыв"}]}'

# ПРАВИЛЬНО - загрузка файла
curl -X POST "http://itsfour-solution.ru/api/v1/predict" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@example_reviews.json;type=application/json"
```

При неправильном использовании API вернет подробную ошибку с инструкциями.

## 🎯 **Как использовать ML анализ**

### 🌐 **Через веб-интерфейс:**
1. Откройте [http://itsfour-solution.ru/](http://itsfour-solution.ru/)
2. Нажмите кнопку "Загрузить файл для анализа"
3. Выберите JSON файл с отзывами
4. Дождитесь обработки (с прогрессбаром)
5. Получите результаты на экране

### 💻 **Через curl (командная строка):**

#### Получить файл с результатами:
```bash
curl -X POST "http://itsfour-solution.ru/api/v1/predict" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@ваш_файл.json;type=application/json" \
  -o "результаты.json"
```

#### Получить JSON ответ:
```bash
curl -X POST "http://itsfour-solution.ru/api/v1/predict/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@ваш_файл.json;type=application/json"
```

**Просто замените `ваш_файл.json` на имя вашего файла!**

## 🎨 Компоненты дашборда

### 1. Панель фильтров (`FilterPanel`)
- Выбор временного периода
- Фильтрация по тональности
- Выбор продукта/услуги
- Настройка интервала группировки

### 2. Круговая диаграмма (`TonalityPieChart`)
- Общее распределение тональностей
- Процентное соотношение
- Интерактивные подсказки
- Детальная статистика

### 3. Список продуктов (`ProductsList`)
- Горизонтальные бары тональностей
- Сортировка по количеству отзывов
- Клик для фильтрации
- Подсказки при наведении

### 4. График динамики (`TonalityDynamicsChart`)
- Линейный график изменений
- Переключение: количество/проценты
- Настраиваемые интервалы (день/неделя/месяц)
- Интерактивные элементы

### 5. Столбчатая диаграмма (`ProductsBarChart`)
- Сравнение продуктов по количеству отзывов
- Сортировка по популярности
- Детальные подсказки

## 🔧 ETL Процесс

### Возможности ETL

- ✅ **Автоматическое создание таблиц**
- ✅ **Валидация данных** отзывов
- ✅ **Дедупликация** по `review_id`
- ✅ **Автоматическое создание** продуктов
- ✅ **Обработка ошибок** и подробное логирование
- ✅ **Построение агрегированной статистики**

### Команды ETL

```bash
# Полная загрузка (данные + статистика)
python run_etl.py

# Только загрузка данных
python run_etl.py --skip-stats

# Только построение статистики
python run_etl.py --skip-load

# С указанием пути к данным
python run_etl.py --data-path /path/to/json/files
```

### Пример вывода ETL

```
🚀 Запуск ETL процесса для дашборда Газпромбанка
📁 Путь к данным: /Users/.../data/raw/banki_ru
🗄️  База данных: postgresql://postgres:postgres@localhost:5432/gazprombank_reviews

📥 Загрузка данных из JSON файлов...
✅ Загрузка данных завершена успешно

📊 Построение агрегированной статистики...
✅ Построение статистики завершено успешно

📈 Сводка по данным:
============================================================
Общая статистика:
  Всего продуктов: 2
  Всего отзывов: 1712
  Положительных: 280 (16.4%)
  Отрицательных: 1386 (81.0%)
  Нейтральных: 46 (2.7%)

По продуктам:
  Кредитные карты: 1448 отзывов (+12.8%, -84.5%, ★1.67)
  Ипотека: 264 отзыва (+36.0%, -61.4%, ★2.57)
============================================================

🎉 ETL процесс успешно завершен!
```

## 🧪 Тестирование

### Backend тестирование

```bash
# Тестирование всех API эндпоинтов
cd backend
python test_api.py

# Ручное тестирование
curl http://localhost:8000/docs  # Swagger UI
curl http://localhost:8000/redoc # ReDoc
```

### Frontend тестирование

```bash
cd frontend
npm run build    # Проверка сборки
npm run lint     # Проверка кода
npm run dev      # Режим разработки
```

## 📊 Результаты и метрики

### 🎯 **Качество ML моделей**
| Модель | Задача | Точность | F1-Score |
|--------|--------|----------|----------|
| **TF-IDF + LR** | Классификация продуктов | 84% | 0.85 |
| **XLM-RoBERTa** | Анализ тональности | 86% | 0.87 |
| **Гибридная система** | Общая точность | **85%** | **0.85** |

### ⚡ **Производительность системы**
| Компонент | Метрика | Значение |
|-----------|---------|----------|
| **API Response** | Время отклика | <100ms |
| **ML Pipeline** | Обработка отзыва | ~200ms |
| **Frontend** | First Contentful Paint | <1.8s |
| **System** | Пропускная способность | 300 отз/мин |

### 📈 **Объем данных**
- **Собранные отзывы**: 58,000+ (Sravni.ru + Banki.ru)
- **Размеченные клаузы**: 46,312 (для обучения ML)
- **Тематические кластеры**: 13 категорий продуктов
- **Временной диапазон**: 2024-2025

### 🛠️ **Технологический стек**
- **Data Science**: Python, Pandas, scikit-learn, PyTorch, Transformers, Ollama
- **Backend**: FastAPI, PostgreSQL, SQLAlchemy, Pydantic, Uvicorn
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Recharts, Axios
- **ML Models**: TF-IDF + Logistic Regression, XLM-RoBERTa Large
- **Infrastructure**: Docker, Docker Compose, Nginx, GitHub Actions

## 🔍 Возможности дашборда

### Фильтрация и анализ
- 📅 **Временные фильтры** - анализ по периодам
- 🏷️ **Фильтры по продуктам** - детальный анализ услуг
- 😊 **Фильтры по тональности** - фокус на конкретных настроениях
- 📊 **Интервалы группировки** - день/неделя/месяц

### Визуализация
- 🥧 **Круговые диаграммы** - общее распределение
- 📈 **Линейные графики** - динамика изменений
- 📊 **Столбчатые диаграммы** - сравнение продуктов
- 🎯 **Горизонтальные бары** - детальная статистика

### Интерактивность
- 🖱️ **Клик по элементам** для фильтрации
- 💡 **Подсказки при наведении** с деталями
- 🔄 **Реактивные обновления** при изменении фильтров
- 📱 **Адаптивный дизайн** для всех устройств

## 🚀 Развертывание

### 🐳 **Docker (Рекомендуется)**

```bash
# Запуск всех сервисов (PostgreSQL + Backend + Frontend + Nginx)
docker-compose up --build -d

# Загрузка данных в базу
docker-compose exec backend python run_etl.py

# Проверка статуса сервисов
docker-compose ps

# Остановка всех сервисов
docker-compose down

# Логи отдельных сервисов
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx
```

**Доступ к сервисам:**
- **Frontend**: http://localhost:3000 (через nginx прокси)
- **Backend API**: http://localhost:8000/api/v1
- **API Docs**: http://localhost:8000/docs

**Production доступ:**
- **🌐 Живая демонстрация**: http://itsfour-solution.ru/
- **📡 Production API**: http://itsfour-solution.ru/api/v1/
- **📚 API Документация**: http://itsfour-solution.ru/api/docs

### ☁️ **Production развертывание**

Подробные инструкции по развертыванию на различных платформах:
- **[📋 DEPLOYMENT.md](DEPLOYMENT.md)** - Полное руководство по деплою
- **Heroku, Railway, Render** - Backend развертывание
- **Vercel, Netlify** - Frontend развертывание
- **Docker Compose** - Локальное production окружение

## 🐛 Устранение неполадок

### Проблемы с подключением к БД

1. Убедитесь, что PostgreSQL запущен:
   ```bash
   brew services start postgresql@14
   ```

2. Проверьте подключение:
   ```bash
   psql -U postgres -d gazprombank_reviews -c "SELECT 1;"
   ```

3. Создайте пользователя, если нужно:
   ```bash
   createuser -s postgres
   ```

### Проблемы с зависимостями

1. **Python зависимости**:
   ```bash
   cd backend
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Node.js зависимости**:
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

### Проблемы с API

1. Проверьте, что backend запущен:
   ```bash
   curl http://localhost:8000/health
   ```

2. Проверьте CORS настройки в `backend/app/config.py`

3. Убедитесь, что переменная окружения установлена:
   ```bash
   echo $NEXT_PUBLIC_API_URL
   ```

## 🎯 Основные возможности

### 📊 **Аналитический дашборд**
- **Круговые диаграммы** распределения тональности
- **Временные графики** динамики настроений  
- **Столбчатые диаграммы** по продуктам
- **Интерактивные фильтры** по датам и продуктам

### 🤖 **ML анализ файлов**
- **Загрузка JSON** файлов с отзывами через веб-интерфейс
- **Гибридная классификация** продуктов (TF-IDF + XLM-RoBERTa)
- **Мультилейбл анализ** тональности по каждому продукту
- **Прогрессбар и таймер** обработки в реальном времени
- **Новый формат ответа** с predictions для интеграции

### 🔍 **Детальная аналитика**
- **Аспектный анализ** по продуктам
- **Статистика по периодам** (день/неделя/месяц)
- **Топ отзывы** по тональности
- **Экспорт результатов** в различных форматах


## 📄 Лицензия

Этот проект создан для хакатона Газпромбанка и предназначен для демонстрационных целей.

## 👥 Команда разработки

Проект разработан командой **IT's Four** в рамках хакатона Газпромбанка.

---

## 📞 Поддержка и контакты

### 🆘 **Техническая поддержка**
Если что-то не работает или возникли вопросы:

**Контакт капитана команды**: [@mishantique](https://t.me/mishantique)

### 📚 **Документация**
- **[📖 Полная документация](docs/README.md)** - Центральный хаб
- **[🚀 Deployment гайд](DEPLOYMENT.md)** - Инструкции по развертыванию
- **[📡 API документация](http://localhost:8000/docs)** - Swagger UI
- **[📋 ReDoc](http://localhost:8000/redoc)** - Альтернативная API документация

### 🔧 **Устранение неполадок**
1. Проверьте раздел "Устранение неполадок" выше
2. Посмотрите логи: `docker-compose logs -f`
3. Убедитесь, что все сервисы запущены: `docker-compose ps`
4. Проверьте health endpoints: `curl http://localhost:8000/health`

---

## 🎉 Заключение

Данный проект демонстрирует полный цикл разработки современной системы анализа данных - от сбора и обработки информации до создания готового продукта с веб-интерфейсом. 

**Ключевые достижения:**
- ✅ **Высокое качество ML** (85% точность гибридной системы)
- ✅ **Современная архитектура** с микросервисами и Docker
- ✅ **Полная автоматизация** от парсинга до ML анализа
- ✅ **Production развертывание** на [itsfour-solution.ru](http://itsfour-solution.ru/)
- ✅ **Готовая система** с мониторингом и документацией

**🌐 [Попробуйте систему в действии →](http://itsfour-solution.ru/)**

**Удачного анализа отзывов! 🚀**

*Проект создан командой IT's Four для хакатона Газпромбанка*