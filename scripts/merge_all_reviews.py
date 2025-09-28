#!/usr/bin/env python3
"""
Скрипт для объединения всех JSON файлов с отзывами в один файл
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_json_files(directory: Path) -> List[Path]:
    """Найти все JSON файлы в директории"""
    json_files = []
    for file_path in directory.glob('*.json'):
        if file_path.is_file():
            json_files.append(file_path)
    return sorted(json_files)

def load_and_validate_json(file_path: Path) -> List[Dict[Any, Any]]:
    """Загрузить и валидировать JSON файл"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            logger.info(f"✓ {file_path.name}: {len(data)} записей")
            return data
        elif isinstance(data, dict) and 'data' in data:
            reviews = data['data']
            logger.info(f"✓ {file_path.name}: {len(reviews)} записей (из поля 'data')")
            return reviews
        else:
            logger.warning(f"⚠ {file_path.name}: неожиданная структура данных")
            return []
    
    except json.JSONDecodeError as e:
        logger.error(f"✗ {file_path.name}: ошибка парсинга JSON - {e}")
        return []
    except Exception as e:
        logger.error(f"✗ {file_path.name}: ошибка чтения файла - {e}")
        return []

def validate_review_structure(review: Dict[Any, Any], file_name: str) -> bool:
    """Проверить структуру отзыва"""
    required_fields = ['review_id', 'review_text', 'review_date', 'product_type']
    
    for field in required_fields:
        if field not in review:
            return False
    
    # Проверяем, что текст отзыва не пустой
    if not review.get('review_text', '').strip():
        return False
    
    return True

def merge_json_files(source_dir: str, output_file: str) -> None:
    """Объединить все JSON файлы в один"""
    source_path = Path(source_dir)
    output_path = Path(output_file)
    
    if not source_path.exists():
        logger.error(f"Директория {source_dir} не существует")
        sys.exit(1)
    
    logger.info(f"Поиск JSON файлов в {source_path}")
    json_files = find_json_files(source_path)
    
    if not json_files:
        logger.error("JSON файлы не найдены")
        sys.exit(1)
    
    logger.info(f"Найдено {len(json_files)} JSON файлов")
    
    all_reviews = []
    stats = {
        'total_files': len(json_files),
        'processed_files': 0,
        'total_reviews': 0,
        'valid_reviews': 0,
        'invalid_reviews': 0,
        'files_stats': {}
    }
    
    for file_path in json_files:
        logger.info(f"Обработка {file_path.name}...")
        
        reviews = load_and_validate_json(file_path)
        if not reviews:
            continue
        
        valid_count = 0
        invalid_count = 0
        
        for review in reviews:
            if validate_review_structure(review, file_path.name):
                all_reviews.append(review)
                valid_count += 1
            else:
                invalid_count += 1
        
        stats['processed_files'] += 1
        stats['valid_reviews'] += valid_count
        stats['invalid_reviews'] += invalid_count
        stats['files_stats'][file_path.name] = {
            'total': len(reviews),
            'valid': valid_count,
            'invalid': invalid_count
        }
        
        logger.info(f"  Валидных отзывов: {valid_count}, невалидных: {invalid_count}")
    
    stats['total_reviews'] = len(all_reviews)
    
    # Создаем директорию для выходного файла если не существует
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Сохраняем объединенный файл
    logger.info(f"Сохранение объединенного файла в {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_reviews, f, ensure_ascii=False, indent=2)
    
    # Сохраняем статистику
    stats_path = output_path.with_suffix('.stats.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    # Выводим итоговую статистику
    logger.info("=" * 50)
    logger.info("ИТОГОВАЯ СТАТИСТИКА")
    logger.info("=" * 50)
    logger.info(f"Обработано файлов: {stats['processed_files']}/{stats['total_files']}")
    logger.info(f"Всего отзывов: {stats['total_reviews']}")
    logger.info(f"Валидных отзывов: {stats['valid_reviews']}")
    logger.info(f"Невалидных отзывов: {stats['invalid_reviews']}")
    logger.info(f"Объединенный файл: {output_path}")
    logger.info(f"Статистика: {stats_path}")
    logger.info("=" * 50)
    
    # Детальная статистика по файлам
    logger.info("СТАТИСТИКА ПО ФАЙЛАМ:")
    for filename, file_stats in stats['files_stats'].items():
        logger.info(f"  {filename}: {file_stats['valid']}/{file_stats['total']} валидных")

def main():
    """Основная функция"""
    if len(sys.argv) != 3:
        print("Использование: python merge_all_reviews.py <source_directory> <output_file>")
        print("Пример: python merge_all_reviews.py data/raw/banki_ru data/raw/all_reviews.json")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    output_file = sys.argv[2]
    
    logger.info("Запуск объединения JSON файлов")
    logger.info(f"Исходная директория: {source_dir}")
    logger.info(f"Выходной файл: {output_file}")
    
    merge_json_files(source_dir, output_file)
    
    logger.info("Объединение завершено успешно!")

if __name__ == "__main__":
    main()
