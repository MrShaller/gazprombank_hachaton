# 🚀 Инструкция по деплою Gazprombank Dashboard

## 📋 Подготовка к деплою

### 1. Настройка переменных окружения

Скопируйте файл `backend/env.example` в `backend/.env` и настройте переменные:

```bash
cp backend/env.example backend/.env
```

**Ключевые переменные для продакшена:**

```env
# Обязательно измените для продакшена!
ENVIRONMENT=production

# URL вашей продакшен базы данных
DATABASE_URL=postgresql://user:password@host:port/dbname

# Домены вашего фронтенда (через запятую)
ADDITIONAL_CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Отключите отладку
DEBUG=false
```

### 2. CORS настройки

CORS автоматически настраивается в зависимости от `ENVIRONMENT`:

- **development**: `localhost:3000`, `127.0.0.1:3000`, `null`
- **staging**: `*-staging.vercel.app`, `*-staging.herokuapp.com` 
- **production**: `*.vercel.app`, `*.herokuapp.com` + `ADDITIONAL_CORS_ORIGINS`

## 🐳 Docker деплой

### Запуск всего стека:

```bash
# Сборка и запуск
docker-compose up --build -d

# Загрузка данных в базу
docker-compose exec backend python run_etl.py /app/data/raw/all_reviews.json /app/data/processed/analysis/products_analysis.json
```

### Переменные для Docker:

```env
ENVIRONMENT=production
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/gazprombank_reviews
ADDITIONAL_CORS_ORIGINS=https://yourdomain.com
```

## ☁️ Деплой на облачные платформы

### Heroku

1. **Backend:**
```bash
# В папке backend/
heroku create gazprombank-api
heroku addons:create heroku-postgresql:mini
heroku config:set ENVIRONMENT=production
heroku config:set ADDITIONAL_CORS_ORIGINS=https://yourfrontend.vercel.app
git push heroku main
```

2. **Загрузка данных:**
```bash
heroku run python run_etl.py /app/data/raw/all_reviews.json /app/data/processed/analysis/products_analysis.json
```

### Railway

1. **Подключите GitHub репозиторий**
2. **Настройте переменные:**
   - `ENVIRONMENT=production`
   - `ADDITIONAL_CORS_ORIGINS=https://yourfrontend.vercel.app`
3. **Railway автоматически создаст PostgreSQL базу**

### Render

1. **Web Service:** подключите GitHub
2. **PostgreSQL:** создайте отдельно
3. **Переменные окружения:**
   ```
   ENVIRONMENT=production
   DATABASE_URL=postgresql://... (из Render PostgreSQL)
   ADDITIONAL_CORS_ORIGINS=https://yourfrontend.vercel.app
   ```

## 🌐 Фронтенд деплой

### Vercel (рекомендуется)

1. **Подключите GitHub репозиторий**
2. **Настройте переменные:**
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.herokuapp.com/api/v1
   ```
3. **Build settings:**
   - Build Command: `cd frontend && npm run build`
   - Output Directory: `frontend/.next`

### Netlify

```bash
# В папке frontend/
npm run build
# Загрузите папку .next на Netlify
```

## 🔒 Безопасность для продакшена

### ✅ Обязательные изменения:

1. **Удалите `"null"` из CORS** (только для разработки)
2. **Используйте HTTPS** для всех доменов
3. **Настройте переменные окружения** вместо хардкода
4. **Смените пароли базы данных**
5. **Включите логирование ошибок**

### 🛡️ Дополнительная безопасность:

```python
# В backend/app/main.py добавьте:
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)
```

## 📊 Мониторинг

### Логи приложения:
```bash
# Docker
docker-compose logs -f backend

# Heroku
heroku logs --tail -a gazprombank-api
```

### Проверка здоровья API:
```bash
curl https://your-backend.herokuapp.com/api/v1/health
```

## 🔧 Troubleshooting

### Проблема: CORS ошибки
**Решение:** Проверьте `ADDITIONAL_CORS_ORIGINS` и `ENVIRONMENT`

### Проблема: База данных недоступна  
**Решение:** Проверьте `DATABASE_URL` и доступность PostgreSQL

### Проблема: 404 на API эндпоинты
**Решение:** Убедитесь что API доступен на `/api/v1/health`

## 📝 Чеклист деплоя

- [ ] Настроены переменные окружения
- [ ] CORS настроен для вашего домена
- [ ] База данных создана и доступна
- [ ] Данные загружены через ETL
- [ ] API отвечает на `/health`
- [ ] Фронтенд подключен к правильному API URL
- [ ] HTTPS настроен для продакшена
- [ ] Мониторинг и логи настроены
