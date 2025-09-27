#!/usr/bin/env python3
"""
Простой скрипт для тестирования API эндпоинтов
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"


def test_endpoint(endpoint, description):
    """Тестирование эндпоинта"""
    print(f"\n🔍 Тестирование: {description}")
    print(f"📡 GET {BASE_URL}{endpoint}")
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}")
        print(f"📊 Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📦 Данных получено: {len(data) if isinstance(data, list) else 'объект'}")
            
            # Показываем первые несколько элементов
            if isinstance(data, list) and data:
                print(f"📋 Пример данных: {json.dumps(data[0], ensure_ascii=False, indent=2)}")
            elif isinstance(data, dict):
                print(f"📋 Данные: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ Ошибка: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться к серверу. Убедитесь, что сервер запущен на http://localhost:8000")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование API дашборда отзывов Газпромбанка")
    print("=" * 60)
    
    # Тестирование основных эндпоинтов
    test_endpoint("/", "Корневой эндпоинт")
    test_endpoint("/health", "Проверка здоровья")
    test_endpoint("/info", "Информация об API")
    
    # Тестирование продуктов
    test_endpoint("/products", "Список продуктов")
    test_endpoint("/products/stats", "Статистика по продуктам")
    
    # Тестирование отзывов
    test_endpoint("/reviews?limit=5", "Список отзывов (первые 5)")
    test_endpoint("/reviews/count", "Количество отзывов")
    
    # Тестирование аналитики
    test_endpoint("/analytics/summary", "Сводная статистика")
    test_endpoint("/analytics/tonality", "Распределение по тональности")
    test_endpoint("/analytics/dynamics?interval=month", "Динамика по месяцам")
    test_endpoint("/analytics/ratings", "Распределение по рейтингам")
    test_endpoint("/analytics/top-reviews?limit=3", "Топ-3 отзыва")
    
    print("\n" + "=" * 60)
    print("✅ Тестирование завершено!")
    print("📖 Полная документация API: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
