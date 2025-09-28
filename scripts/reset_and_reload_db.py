#!/usr/bin/env python3
"""
Скрипт для полной перезагрузки базы данных
1. Удаляет все таблицы
2. Создает таблицы заново
3. Загружает данные из объединенного файла
"""

import sys
import os
import logging
from pathlib import Path

# Добавляем путь к backend в PYTHONPATH
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from app.database import engine, Base, get_db
from app.utils.etl_loader import ReviewETL
from app.utils.stats_builder import StatsBuilder
from sqlalchemy import text
import json

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def drop_all_tables():
    """Удалить все таблицы"""
    logger.info("Удаление всех таблиц...")
    
    try:
        with engine.connect() as conn:
            # Получаем список всех таблиц
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if not tables:
                logger.info("Таблицы не найдены")
                return
            
            logger.info(f"Найдено таблиц: {len(tables)}")
            for table in tables:
                logger.info(f"  - {table}")
            
            # Удаляем все таблицы с CASCADE
            for table in tables:
                logger.info(f"Удаление таблицы {table}...")
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            
            conn.commit()
            logger.info("✓ Все таблицы успешно удалены")
            
    except Exception as e:
        logger.error(f"Ошибка при удалении таблиц: {e}")
        raise

def check_file_exists(file_path: str) -> bool:
    """Проверить существование файла"""
    path = Path(file_path)
    if not path.exists():
        logger.error(f"Файл не найден: {file_path}")
        return False
    
    if not path.is_file():
        logger.error(f"Путь не является файлом: {file_path}")
        return False
    
    # Проверяем размер файла
    size_mb = path.stat().st_size / (1024 * 1024)
    logger.info(f"Размер файла: {size_mb:.2f} МБ")
    
    return True

def get_file_stats(file_path: str) -> dict:
    """Получить статистику файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return {
                'total_records': len(data),
                'structure': 'array'
            }
        elif isinstance(data, dict):
            return {
                'total_records': len(data.get('data', [])) if 'data' in data else 0,
                'structure': 'object_with_data' if 'data' in data else 'object',
                'keys': list(data.keys())
            }
        else:
            return {
                'total_records': 0,
                'structure': 'unknown'
            }
    except Exception as e:
        logger.error(f"Ошибка анализа файла: {e}")
        return {'error': str(e)}

def reset_and_reload_database(json_file_path: str):
    """Полная перезагрузка базы данных"""
    logger.info("=" * 60)
    logger.info("НАЧАЛО ПЕРЕЗАГРУЗКИ БАЗЫ ДАННЫХ")
    logger.info("=" * 60)
    
    # Проверяем файл
    if not check_file_exists(json_file_path):
        sys.exit(1)
    
    # Получаем статистику файла
    file_stats = get_file_stats(json_file_path)
    logger.info(f"Статистика файла: {file_stats}")
    
    try:
        # Шаг 1: Удаляем все таблицы
        logger.info("\n" + "=" * 40)
        logger.info("ШАГ 1: УДАЛЕНИЕ ТАБЛИЦ")
        logger.info("=" * 40)
        drop_all_tables()
        
        # Шаг 2: Создаем таблицы заново
        logger.info("\n" + "=" * 40)
        logger.info("ШАГ 2: СОЗДАНИЕ ТАБЛИЦ")
        logger.info("=" * 40)
        etl = ReviewETL()
        etl.create_tables()
        logger.info("✓ Таблицы успешно созданы")
        
        # Шаг 3: Загружаем данные
        logger.info("\n" + "=" * 40)
        logger.info("ШАГ 3: ЗАГРУЗКА ДАННЫХ")
        logger.info("=" * 40)
        logger.info(f"Загрузка данных из {json_file_path}")
        
        reviews_loaded = etl.load_reviews_from_json(json_file_path)
        result = etl.stats
        
        logger.info(f"✓ Загружено продуктов: {result['products_created']}")
        logger.info(f"✓ Загружено отзывов: {result['reviews_loaded']}")
        logger.info(f"✓ Пропущено отзывов: {result['reviews_skipped']}")
        logger.info(f"✓ Ошибок: {result['errors']}")
        
        # Шаг 4: Построение статистики
        logger.info("\n" + "=" * 40)
        logger.info("ШАГ 4: ПОСТРОЕНИЕ СТАТИСТИКИ")
        logger.info("=" * 40)
        stats_builder = StatsBuilder()
        stats_result = stats_builder.build_daily_stats()
        logger.info(f"✓ Создано записей статистики: {stats_result.get('records_created', 0)}")
        
        # Итоговая статистика
        logger.info("\n" + "=" * 60)
        logger.info("ИТОГОВАЯ СТАТИСТИКА")
        logger.info("=" * 60)
        logger.info(f"Исходный файл: {json_file_path}")
        logger.info(f"Записей в файле: {file_stats.get('total_records', 'неизвестно')}")
        logger.info(f"Продуктов создано: {result['products_created']}")
        logger.info(f"Отзывов загружено: {result['reviews_loaded']}")
        logger.info(f"Отзывов пропущено: {result['reviews_skipped']}")
        logger.info(f"Ошибок: {result['errors']}")
        logger.info(f"Статистических записей: {stats_result.get('records_created', 0)}")
        logger.info("=" * 60)
        logger.info("ПЕРЕЗАГРУЗКА ЗАВЕРШЕНА УСПЕШНО!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Ошибка при перезагрузке базы данных: {e}")
        logger.error("ПЕРЕЗАГРУЗКА ПРЕРВАНА!")
        raise

def main():
    """Основная функция"""
    if len(sys.argv) < 2:
        print("Использование: python reset_and_reload_db.py <json_file_path> [--force]")
        print("Пример: python reset_and_reload_db.py data/raw/all_reviews.json --force")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    force = len(sys.argv) > 2 and sys.argv[2] == '--force'
    
    # Подтверждение операции
    if not force:
        print("⚠️  ВНИМАНИЕ: Эта операция удалит ВСЕ данные из базы данных!")
        print(f"Файл для загрузки: {json_file_path}")
        
        try:
            response = input("Продолжить? (yes/no): ").lower().strip()
            if response not in ['yes', 'y', 'да']:
                print("Операция отменена")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print("\nОперация отменена")
            sys.exit(0)
    else:
        print("⚠️  ПРИНУДИТЕЛЬНАЯ ПЕРЕЗАГРУЗКА БАЗЫ ДАННЫХ")
        print(f"Файл для загрузки: {json_file_path}")
    
    reset_and_reload_database(json_file_path)

if __name__ == "__main__":
    main()
