#!/usr/bin/env python3
"""
Удобный скрипт для запуска ETL процессов
"""
import os
import sys
import argparse
from pathlib import Path

# Добавляем путь к приложению
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.etl_loader import ReviewETL
from app.utils.stats_builder import StatsBuilder


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='ETL для загрузки данных отзывов')
    parser.add_argument(
        '--data-path', 
        default='/Users/mishantique/Desktop/Projects/gazprombank_hachaton/data/raw/banki_ru',
        help='Путь к директории с JSON файлами'
    )
    parser.add_argument(
        '--db-url',
        default='postgresql://postgres:postgres@localhost:5432/gazprombank_reviews',
        help='URL подключения к базе данных'
    )
    parser.add_argument(
        '--skip-load',
        action='store_true',
        help='Пропустить загрузку данных, только построить статистику'
    )
    parser.add_argument(
        '--skip-stats',
        action='store_true',
        help='Пропустить построение статистики'
    )
    parser.add_argument(
        '--aspects-path',
        default='/Users/mishantique/Desktop/Projects/gazprombank_hachaton/data/processed/analysis/products_analysis.json',
        help='Путь к JSON файлу с анализом аспектов продуктов'
    )
    parser.add_argument(
        '--skip-aspects',
        action='store_true',
        help='Пропустить загрузку анализа аспектов'
    )
    
    args = parser.parse_args()
    
    print("🚀 Запуск ETL процесса для дашборда Газпромбанка")
    print(f"📁 Путь к данным: {args.data_path}")
    print(f"🔍 Путь к анализу аспектов: {args.aspects_path}")
    print(f"🗄️  База данных: {args.db_url}")
    print()
    
    # Проверка существования директории с данными
    if not args.skip_load and not Path(args.data_path).exists():
        print(f"❌ Директория с данными не найдена: {args.data_path}")
        sys.exit(1)
    
    success = True
    
    # Загрузка данных
    if not args.skip_load:
        print("📥 Загрузка данных из JSON файлов...")
        etl = ReviewETL(args.db_url)
        stats = etl.load_all_json_files(args.data_path)
        
        if stats['errors'] > 0:
            print(f"⚠️  Загрузка завершилась с {stats['errors']} ошибками")
            success = False
        else:
            print("✅ Загрузка данных завершена успешно")
    
    # Загрузка анализа аспектов
    if not args.skip_aspects:
        print("\n🔍 Загрузка анализа аспектов продуктов...")
        if not Path(args.aspects_path).exists():
            print(f"⚠️  Файл анализа аспектов не найден: {args.aspects_path}")
            print("   Пропускаем загрузку аспектов...")
        else:
            etl = ReviewETL(args.db_url)
            aspects_count = etl.load_aspects_from_json(args.aspects_path)
            
            if etl.stats['errors'] > 0:
                print(f"⚠️  Загрузка аспектов завершилась с {etl.stats['errors']} ошибками")
                success = False
            else:
                print(f"✅ Загрузка аспектов завершена: {aspects_count} записей")
    
    # Построение статистики
    if not args.skip_stats:
        print("\n📊 Построение агрегированной статистики...")
        builder = StatsBuilder(args.db_url)
        stats = builder.build_daily_stats()
        
        if stats['errors'] > 0:
            print(f"⚠️  Построение статистики завершилось с {stats['errors']} ошибками")
            success = False
        else:
            print("✅ Построение статистики завершено успешно")
        
        # Вывод сводки
        print("\n📈 Сводка по данным:")
        builder.print_summary()
    
    if success:
        print("\n🎉 ETL процесс успешно завершен!")
        sys.exit(0)
    else:
        print("\n❌ ETL процесс завершился с ошибками")
        sys.exit(1)


if __name__ == "__main__":
    main()
