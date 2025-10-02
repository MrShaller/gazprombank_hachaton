FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev python3-dev build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Установка python-зависимостей
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Загружаем NLTK стоп-слова
RUN python -m nltk.downloader stopwords

# Копируем код backend
COPY backend ./backend

# Копируем scripts (они должны быть в /app/scripts)
COPY scripts ./scripts

# Рабочая директория = backend
WORKDIR /app/backend

EXPOSE 8000

# Запуск uvicorn (или меняй на run_server.py, если там своя логика)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
