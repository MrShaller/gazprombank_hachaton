# 🏦 Газпромбанк | Дашборд анализа тональности отзывов

Полнофункциональный дашборд для анализа клиентских отзывов о продуктах Газпромбанка с визуализацией тональности, динамики и статистики.

![Дашборд](logo-gazprombank.png)

## 🎯 Описание проекта

Система предназначена для анализа отзывов клиентов Газпромбанка, собранных с различных платформ (banki.ru, sravni.ru). Дашборд предоставляет:

- **Анализ тональности** отзывов (положительно/отрицательно/нейтрально)
- **Визуализацию данных** через интерактивные графики
- **Фильтрацию** по продуктам, датам и тональности
- **Динамику изменений** по времени
- **Детальную статистику** по каждому продукту

## 🏗️ Архитектура

```
gazprombank_hachaton/
├── 📊 data/                    # Исходные данные
│   ├── raw/banki_ru/          # JSON файлы отзывов
│   └── processed/             # Обработанные данные
├── 🐍 backend/                # FastAPI backend
│   ├── app/                   # Основное приложение
│   │   ├── models.py          # SQLAlchemy модели
│   │   ├── schemas.py         # Pydantic схемы
│   │   ├── crud.py            # CRUD операции
│   │   ├── main.py            # FastAPI приложение
│   │   └── routers/           # API роутеры
│   ├── run_etl.py             # ETL скрипт
│   └── run_server.py          # Запуск сервера
├── ⚛️ frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/               # Next.js App Router
│   │   ├── components/        # React компоненты
│   │   ├── lib/               # API клиент
│   │   └── types/             # TypeScript типы
│   └── package.json
└── 📜 scripts/                # Вспомогательные скрипты
```

## 🚀 Быстрый старт

### Предварительные требования

- **Python 3.13+**
- **Node.js 18+**
- **PostgreSQL 14+**
- **Git**

### 1️⃣ Клонирование репозитория

```bash
git clone <repository-url>
cd gazprombank_hachaton
```

### 2️⃣ Настройка PostgreSQL

```bash
# Установка PostgreSQL (macOS)
brew install postgresql@14
brew services start postgresql@14

# Создание пользователя и базы данных
createuser -s postgres
createdb gazprombank_reviews
```

### 3️⃣ Настройка Backend

```bash
# Переход в папку backend
cd backend

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# или venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Загрузка данных в БД
python run_etl.py

# Запуск сервера
python run_server.py
```

Backend будет доступен на: http://localhost:8000

### 4️⃣ Настройка Frontend

```bash
# Переход в папку frontend
cd ../frontend

# Установка зависимостей
npm install

# Создание файла переменных окружения
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# Запуск в режиме разработки
npm run dev
```

Frontend будет доступен на: http://localhost:3000

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

### Служебные
- `GET /` - информация об API
- `GET /health` - проверка здоровья сервиса
- `GET /api/v1/health` - проверка здоровья API

### Примеры запросов

```bash
# Получить статистику по продуктам
curl http://localhost:8000/api/v1/products/stats

# Получить распределение тональности для продукта
curl "http://localhost:8000/api/v1/analytics/tonality?product_id=1"

# Получить динамику по месяцам
curl "http://localhost:8000/api/v1/analytics/dynamics?interval=month"

# Получить топ положительных отзывов
curl "http://localhost:8000/api/v1/analytics/top-reviews?tonality=положительно&limit=5"
```

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

## 📊 Статистика проекта

### Загруженные данные
- **Всего отзывов**: 1,712
- **Продуктов**: 2 (Кредитные карты, Ипотека)
- **Временной диапазон**: 2024-2025
- **Источники**: banki.ru

### Распределение тональностей
- **Отрицательные**: 81.0% (1,386 отзывов)
- **Положительные**: 16.4% (280 отзывов)
- **Нейтральные**: 2.7% (46 отзывов)

### Технические характеристики
- **Backend**: Python, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **Визуализация**: Recharts
- **База данных**: PostgreSQL с индексами
- **API**: RESTful с полной документацией

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

### Локальная разработка

1. Следуйте инструкциям в разделе "Быстрый старт"
2. Backend: http://localhost:8000
3. Frontend: http://localhost:3000

### Production развертывание

```bash
# Backend
cd backend
pip install -r requirements.txt
python run_etl.py
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Frontend
cd frontend
npm run build
npm start
```

### Docker (планируется)

```bash
# Запуск всех сервисов
docker-compose up -d

# Остановка
docker-compose down
```

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

## 📚 Документация

### API документация
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Структура кода
- **Backend**: `/backend/README.md`
- **Frontend**: `/frontend/README.md`

## 🤝 Участие в разработке

### Структура коммитов
```
feat: добавить новый компонент графика
fix: исправить ошибку подключения к API
docs: обновить README
style: форматирование кода
refactor: рефакторинг API клиента
test: добавить тесты для ETL
```

### Локальная разработка
1. Форкните репозиторий
2. Создайте ветку: `git checkout -b feature/new-feature`
3. Внесите изменения
4. Запустите тесты: `npm test` / `pytest`
5. Создайте Pull Request

## 📄 Лицензия

Этот проект создан для хакатона Газпромбанка и предназначен для демонстрационных целей.

## 👥 Команда

- **Backend разработка**: Python, FastAPI, PostgreSQL
- **Frontend разработка**: Next.js, React, TypeScript
- **Дизайн системы**: Архитектура, ETL, API дизайн
- **Визуализация данных**: Recharts, интерактивные графики

---

## 📞 Поддержка

Если у вас есть вопросы или проблемы:

1. Проверьте раздел "Устранение неполадок"
2. Посмотрите логи backend и frontend
3. Убедитесь, что все сервисы запущены
4. Проверьте версии Python и Node.js

**Удачного анализа отзывов! 🚀**