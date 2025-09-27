# 🐳 Docker Setup для Газпромбанк Дашборда

Полная инструкция по развертыванию дашборда с помощью Docker Compose.

## 🚀 Быстрый запуск с Docker

### Предварительные требования

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Git**

### 1. Клонирование и запуск

```bash
# Клонирование репозитория
git clone <repository-url>
cd gazprombank_hachaton

# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f
```

### 2. Доступ к сервисам

После запуска сервисы будут доступны по адресам:

- **🌐 Frontend (Дашборд)**: http://localhost:3000
- **🔧 Backend API**: http://localhost:8000
- **📖 API Документация**: http://localhost:8000/docs
- **🗄️ PostgreSQL**: localhost:5432

## 📋 Управление сервисами

### Основные команды

```bash
# Запуск в фоновом режиме
docker-compose up -d

# Остановка всех сервисов
docker-compose down

# Перезапуск конкретного сервиса
docker-compose restart backend

# Просмотр статуса сервисов
docker-compose ps

# Просмотр логов
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# Просмотр логов в реальном времени
docker-compose logs -f backend
```

### Управление данными

```bash
# Полная очистка (включая данные БД)
docker-compose down -v

# Пересборка образов
docker-compose build --no-cache

# Запуск только ETL для загрузки данных
docker-compose run --rm etl
```

## 🏗️ Архитектура Docker

### Сервисы

1. **postgres** - База данных PostgreSQL 14
2. **backend** - FastAPI приложение
3. **frontend** - Next.js приложение
4. **etl** - Одноразовый сервис загрузки данных

### Сеть и тома

```yaml
networks:
  gazprombank_network:  # Внутренняя сеть для сервисов

volumes:
  postgres_data:        # Постоянное хранилище БД
```

### Порты

- `3000:3000` - Frontend
- `8000:8000` - Backend API
- `5432:5432` - PostgreSQL

## 🔧 Конфигурация

### Переменные окружения

Основные переменные настраиваются в `docker-compose.yml`:

```yaml
# Backend
DATABASE_URL: postgresql://postgres:postgres@postgres:5432/gazprombank_reviews
DEBUG: "false"
APP_NAME: "Gazprombank Reviews Dashboard API"

# Frontend  
NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1
NODE_ENV: production
```

### Кастомизация

Для изменения конфигурации создайте `.env` файл:

```bash
# .env
POSTGRES_PASSWORD=your_secure_password
API_PORT=8001
FRONTEND_PORT=3001
```

Затем обновите `docker-compose.yml`:

```yaml
postgres:
  environment:
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}

backend:
  ports:
    - "${API_PORT:-8000}:8000"

frontend:
  ports:
    - "${FRONTEND_PORT:-3000}:3000"
```

## 🐛 Устранение неполадок

### Проверка состояния сервисов

```bash
# Проверка всех сервисов
docker-compose ps

# Проверка здоровья
curl http://localhost:8000/health
curl http://localhost:3000

# Проверка подключения к БД
docker-compose exec postgres psql -U postgres -d gazprombank_reviews -c "SELECT COUNT(*) FROM reviews;"
```

### Частые проблемы

#### 1. Сервис не запускается

```bash
# Просмотр логов
docker-compose logs service_name

# Пересборка образа
docker-compose build --no-cache service_name
docker-compose up -d service_name
```

#### 2. База данных недоступна

```bash
# Проверка PostgreSQL
docker-compose exec postgres pg_isready -U postgres

# Перезапуск БД
docker-compose restart postgres

# Проверка данных
docker-compose exec postgres psql -U postgres -d gazprombank_reviews -c "\dt"
```

#### 3. Frontend не подключается к API

```bash
# Проверка переменных окружения
docker-compose exec frontend env | grep API

# Проверка сетевого подключения
docker-compose exec frontend curl http://backend:8000/health
```

#### 4. Проблемы с портами

```bash
# Проверка занятых портов
lsof -i :3000
lsof -i :8000
lsof -i :5432

# Изменение портов в docker-compose.yml
ports:
  - "3001:3000"  # Изменить внешний порт
```

### Логи и отладка

```bash
# Детальные логи всех сервисов
docker-compose logs --timestamps

# Логи конкретного сервиса
docker-compose logs -f backend

# Вход в контейнер для отладки
docker-compose exec backend bash
docker-compose exec frontend sh

# Проверка ресурсов
docker stats
```

## 🔄 Обновление

### Обновление кода

```bash
# Остановка сервисов
docker-compose down

# Обновление кода
git pull origin main

# Пересборка и запуск
docker-compose build
docker-compose up -d
```

### Обновление данных

```bash
# Запуск ETL для обновления данных
docker-compose run --rm etl

# Или полная перезагрузка
docker-compose down -v
docker-compose up -d
```

## 📊 Мониторинг

### Health checks

Все сервисы имеют встроенные проверки здоровья:

```bash
# Проверка статуса
docker-compose ps

# Ручная проверка
curl http://localhost:8000/health
curl http://localhost:3000
```

### Метрики

```bash
# Использование ресурсов
docker stats

# Размер образов
docker images | grep gazprombank

# Использование томов
docker volume ls
docker system df
```

## 🚀 Production развертывание

### Рекомендации для продакшена

1. **Безопасность**:
   ```yaml
   postgres:
     environment:
       POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # Из переменной окружения
   ```

2. **Ресурсы**:
   ```yaml
   backend:
     deploy:
       resources:
         limits:
           memory: 512M
           cpus: '0.5'
   ```

3. **Логирование**:
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

4. **Backup БД**:
   ```bash
   # Создание бэкапа
   docker-compose exec postgres pg_dump -U postgres gazprombank_reviews > backup.sql
   
   # Восстановление
   docker-compose exec postgres psql -U postgres gazprombank_reviews < backup.sql
   ```

## 📝 Заключение

Docker Compose упрощает развертывание всей системы одной командой. Все сервисы настроены с правильными зависимостями, health checks и автоматическими перезапусками.

**Для быстрого старта просто выполните:**

```bash
git clone <repository-url>
cd gazprombank_hachaton
docker-compose up -d
```

И откройте http://localhost:3000 для доступа к дашборду! 🎉
