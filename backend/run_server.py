#!/usr/bin/env python3
"""
Скрипт для запуска FastAPI сервера
"""
import uvicorn
import sys
import os

# Добавляем путь к приложению
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

if __name__ == "__main__":
    # Запуск сервера
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Автоперезагрузка при изменении файлов
        log_level="info",
        reload_dirs=["app"]  # Отслеживание изменений только в папке app
    )
