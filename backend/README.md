# 🏦 Gazprombank Reviews Dashboard - Backend

Backend для дашборда анализа клиентских отзывов о продуктах Газпромбанка.

## 🌐 **Production**
**🚀 API доступно по адресу**: http://itsfour-solution.ru/api/v1/  
**📚 Документация**: http://itsfour-solution.ru/api/docs

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# или venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Настройка PostgreSQL

Создайте базу данных:
```sql
CREATE DATABASE gazprombank_reviews;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE gazprombank_reviews TO postgres;
```

### 3. Настройка переменных окружения

Создайте файл `.env`:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gazprombank_reviews
DEBUG=True
```

### 4. Загрузка данных

Запустите ETL для загрузки данных из JSON файлов:

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

## 📊 Структура данных

### Таблицы

1. **products** - Продукты/услуги банка
   - `id` - Уникальный идентификатор
   - `name` - Название продукта
   - `created_at` - Дата создания

2. **reviews** - Отзывы клиентов
   - `id` - Уникальный идентификатор
   - `review_id` - ID отзыва из источника
   - `product_id` - Связь с продуктом
   - `review_text` - Текст отзыва
   - `review_date` - Дата отзыва
   - `rating` - Рейтинг (1-5)
   - `tonality` - Тональность (положительно/отрицательно/нейтрально)
   - `is_valid` - Валидность отзыва

3. **review_stats** - Предварительно агрегированная статистика
   - `product_id` - ID продукта
   - `date` - Дата агрегации
   - `tonality` - Тональность
   - `count` - Количество отзывов
   - `avg_rating` - Средний рейтинг

### Формат JSON данных

```json
{
  "review_id": "12345",
  "review_text": "Отличный банк!",
  "review_date": "31.05.2025 14:52",
  "url": "https://example.com/review/12345",
  "parsed_at": "2025-09-27T15:06:33.492134",
  "bank_name": "gazprombank",
  "product_type": "Ипотека",
  "rating": 5,
  "tonality": "положительно",
  "validation": "Отзыв проверен",
  "is_valid": true
}
```

## 🛠️ Разработка

### Структура проекта

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py          # Настройки приложения
│   ├── database.py        # Подключение к БД
│   ├── models.py          # SQLAlchemy модели
│   ├── schemas.py         # Pydantic схемы
│   └── utils/
│       ├── __init__.py
│       ├── etl_loader.py  # ETL для загрузки данных
│       └── stats_builder.py # Построение статистики
├── run_etl.py            # Скрипт запуска ETL
├── requirements.txt      # Зависимости
└── README.md
```

### Команды разработки

```bash
# Установка зависимостей для разработки
pip install -r requirements.txt

# Форматирование кода
black app/
isort app/

# Проверка линтером
flake8 app/

# Тестирование
pytest
```

## 🔧 ETL процесс

### Возможности ETL

- ✅ Автоматическое создание таблиц
- ✅ Валидация данных отзывов
- ✅ Дедупликация по `review_id`
- ✅ Автоматическое создание продуктов
- ✅ Обработка ошибок и логирование
- ✅ Построение агрегированной статистики
- ✅ Подробная статистика загрузки

### Логи ETL

ETL выводит подробные логи:
```
2025-09-27 15:30:00 - INFO - Загрузка данных из файла: data/raw/banki_ru/ipoteka.json
2025-09-27 15:30:01 - INFO - Создан новый продукт: Ипотека
2025-09-27 15:30:05 - INFO - Загружено 100 отзывов из data/raw/banki_ru/ipoteka.json
...
2025-09-27 15:30:30 - INFO - ИТОГОВАЯ СТАТИСТИКА ЗАГРУЗКИ:
2025-09-27 15:30:30 - INFO - Продуктов создано: 2
2025-09-27 15:30:30 - INFO - Отзывов загружено: 15430
2025-09-27 15:30:30 - INFO - Отзывов пропущено: 0
2025-09-27 15:30:30 - INFO - Ошибок: 0
```

## 🐛 Устранение неполадок

### Проблемы с подключением к БД

1. Убедитесь, что PostgreSQL запущен
2. Проверьте правильность `DATABASE_URL`
3. Убедитесь, что база данных создана

### Ошибки при загрузке данных

1. Проверьте формат JSON файлов
2. Убедитесь в правильности путей к файлам
3. Проверьте логи ETL для деталей ошибок

## 🚀 Запуск API сервера

### Метод 1: Через скрипт
```bash
cd backend
python run_server.py
```

### Метод 2: Через uvicorn
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Метод 3: Через FastAPI CLI
```bash
cd backend
fastapi dev app/main.py
```

После запуска API будет доступно по адресам:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API**: http://localhost:8000/api/v1/

## 📡 API Эндпоинты

### Продукты
- `GET /api/v1/products` - список всех продуктов
- `GET /api/v1/products/stats` - продукты с статистикой
- `GET /api/v1/products/{id}` - продукт по ID

### Отзывы  
- `GET /api/v1/reviews` - список отзывов (с фильтрацией)
- `GET /api/v1/reviews/count` - количество отзывов
- `GET /api/v1/reviews/{id}` - отзыв по ID

### Аналитика
- `GET /api/v1/analytics/summary` - общая сводка
- `GET /api/v1/analytics/tonality` - распределение по тональности
- `GET /api/v1/analytics/dynamics` - динамика по времени
- `GET /api/v1/analytics/ratings` - распределение по рейтингам
- `GET /api/v1/analytics/top-reviews` - топ отзывы

### ML Анализ
- `POST /api/v1/predict/` - анализ тональности JSON файла
- `GET /api/v1/predict/health` - проверка ML сервиса

### Служебные
- `GET /` - информация об API
- `GET /health` - проверка здоровья
- `GET /api/v1/health` - проверка здоровья API

## 🧪 Тестирование API

```bash
# Тестирование всех эндпоинтов
python test_api.py

# Ручное тестирование
curl http://localhost:8000/api/v1/products/stats
curl "http://localhost:8000/api/v1/analytics/tonality?product_id=1"

# Тестирование ML API (локально)
curl -X POST "http://localhost:8000/api/v1/predict/" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_reviews.json"

# Тестирование ML API (production)
curl -X POST "http://itsfour-solution.ru/api/v1/predict/" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_reviews.json"
```

### Пример ML API ответа:

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
    }
  ]
}
```

## 📈 Следующие шаги

1. ✅ Структура БД и модели
2. ✅ ETL для загрузки данных  
3. ✅ FastAPI backend с эндпоинтами
4. ⏳ React frontend
5. ⏳ Docker контейнеризация
