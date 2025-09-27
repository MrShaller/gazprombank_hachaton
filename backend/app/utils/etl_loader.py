"""
ETL скрипт для загрузки JSON данных в PostgreSQL
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import logging

# Добавляем путь к модулям приложения
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from models import Base, Product, Review
from config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReviewETL:
    """ETL класс для загрузки отзывов из JSON в PostgreSQL"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Инициализация ETL загрузчика
        
        Args:
            database_url: URL подключения к БД (если не указан, берется из настроек)
        """
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Статистика загрузки
        self.stats = {
            'products_created': 0,
            'products_existing': 0,
            'reviews_loaded': 0,
            'reviews_skipped': 0,
            'errors': 0
        }
    
    def create_tables(self):
        """Создание таблиц в БД"""
        logger.info("Создание таблиц в базе данных...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Таблицы созданы успешно")
    
    def get_or_create_product(self, session, product_name: str) -> Product:
        """
        Получить существующий продукт или создать новый
        
        Args:
            session: Сессия SQLAlchemy
            product_name: Название продукта
            
        Returns:
            Product: Объект продукта
        """
        # Попытка найти существующий продукт
        product = session.query(Product).filter(Product.name == product_name).first()
        
        if product:
            self.stats['products_existing'] += 1
            return product
        
        # Создание нового продукта
        product = Product(name=product_name)
        session.add(product)
        session.flush()  # Получить ID без коммита
        self.stats['products_created'] += 1
        logger.info(f"Создан новый продукт: {product_name}")
        
        return product
    
    def parse_review_date(self, date_str: str) -> datetime:
        """
        Парсинг даты отзыва из строки
        
        Args:
            date_str: Строка с датой в формате "DD.MM.YYYY HH:MM"
            
        Returns:
            datetime: Объект datetime
        """
        try:
            return datetime.strptime(date_str, "%d.%m.%Y %H:%M")
        except ValueError:
            logger.warning(f"Не удалось распарсить дату: {date_str}")
            return datetime.now()
    
    def parse_parsed_at(self, parsed_at_str: str) -> datetime:
        """
        Парсинг времени парсинга из строки
        
        Args:
            parsed_at_str: Строка с временем парсинга в ISO формате
            
        Returns:
            datetime: Объект datetime
        """
        try:
            return datetime.fromisoformat(parsed_at_str.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Не удалось распарсить время парсинга: {parsed_at_str}")
            return datetime.now()
    
    def validate_review_data(self, review_data: Dict) -> bool:
        """
        Валидация данных отзыва
        
        Args:
            review_data: Словарь с данными отзыва
            
        Returns:
            bool: True если данные валидны
        """
        required_fields = [
            'review_id', 'review_text', 'review_date', 'bank_name',
            'product_type', 'rating', 'tonality', 'parsed_at'
        ]
        
        # Проверка обязательных полей
        for field in required_fields:
            if field not in review_data or not review_data[field]:
                logger.warning(f"Отсутствует обязательное поле: {field}")
                return False
        
        # Проверка рейтинга
        rating = review_data.get('rating')
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            logger.warning(f"Некорректный рейтинг: {rating}")
            return False
        
        # Проверка тональности
        tonality = review_data.get('tonality')
        allowed_tonalities = ['положительно', 'отрицательно', 'нейтрально']
        if tonality not in allowed_tonalities:
            logger.warning(f"Некорректная тональность: {tonality}")
            return False
        
        return True
    
    def load_reviews_from_json(self, json_file_path: str) -> int:
        """
        Загрузка отзывов из JSON файла
        
        Args:
            json_file_path: Путь к JSON файлу
            
        Returns:
            int: Количество загруженных отзывов
        """
        logger.info(f"Загрузка данных из файла: {json_file_path}")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                reviews_data = json.load(file)
        except Exception as e:
            logger.error(f"Ошибка чтения файла {json_file_path}: {e}")
            self.stats['errors'] += 1
            return 0
        
        if not isinstance(reviews_data, list):
            logger.error(f"Файл {json_file_path} содержит некорректный формат данных")
            self.stats['errors'] += 1
            return 0
        
        loaded_count = 0
        session = self.SessionLocal()
        
        try:
            for review_data in reviews_data:
                try:
                    # Валидация данных
                    if not self.validate_review_data(review_data):
                        self.stats['reviews_skipped'] += 1
                        continue
                    
                    # Проверка на дубликат по review_id
                    existing_review = session.query(Review).filter(
                        Review.review_id == review_data['review_id']
                    ).first()
                    
                    if existing_review:
                        self.stats['reviews_skipped'] += 1
                        continue
                    
                    # Получение или создание продукта
                    product = self.get_or_create_product(session, review_data['product_type'])
                    
                    # Создание отзыва
                    review = Review(
                        review_id=review_data['review_id'],
                        product_id=product.id,
                        review_text=review_data['review_text'],
                        review_date=self.parse_review_date(review_data['review_date']),
                        url=review_data.get('url'),
                        parsed_at=self.parse_parsed_at(review_data['parsed_at']),
                        bank_name=review_data['bank_name'],
                        rating=review_data['rating'],
                        tonality=review_data['tonality'],
                        validation=review_data.get('validation'),
                        is_valid=review_data.get('is_valid', True)
                    )
                    
                    session.add(review)
                    loaded_count += 1
                    self.stats['reviews_loaded'] += 1
                    
                    # Коммит каждые 100 записей
                    if loaded_count % 100 == 0:
                        session.commit()
                        logger.info(f"Загружено {loaded_count} отзывов из {json_file_path}")
                
                except Exception as e:
                    logger.error(f"Ошибка обработки отзыва {review_data.get('review_id', 'unknown')}: {e}")
                    self.stats['errors'] += 1
                    session.rollback()
            
            # Финальный коммит
            session.commit()
            logger.info(f"Завершена загрузка из {json_file_path}: {loaded_count} отзывов")
            
        except Exception as e:
            logger.error(f"Критическая ошибка при загрузке из {json_file_path}: {e}")
            session.rollback()
            self.stats['errors'] += 1
            
        finally:
            session.close()
        
        return loaded_count
    
    def load_all_json_files(self, data_directory: str) -> Dict:
        """
        Загрузка всех JSON файлов из директории
        
        Args:
            data_directory: Путь к директории с JSON файлами
            
        Returns:
            Dict: Статистика загрузки
        """
        logger.info(f"Начало загрузки данных из директории: {data_directory}")
        
        # Создание таблиц
        self.create_tables()
        
        # Поиск всех JSON файлов
        json_files = list(Path(data_directory).glob("*.json"))
        
        if not json_files:
            logger.warning(f"Не найдено JSON файлов в директории: {data_directory}")
            return self.stats
        
        logger.info(f"Найдено {len(json_files)} JSON файлов")
        
        # Загрузка каждого файла
        for json_file in json_files:
            self.load_reviews_from_json(str(json_file))
        
        # Вывод итоговой статистики
        logger.info("=" * 50)
        logger.info("ИТОГОВАЯ СТАТИСТИКА ЗАГРУЗКИ:")
        logger.info(f"Продуктов создано: {self.stats['products_created']}")
        logger.info(f"Продуктов найдено существующих: {self.stats['products_existing']}")
        logger.info(f"Отзывов загружено: {self.stats['reviews_loaded']}")
        logger.info(f"Отзывов пропущено: {self.stats['reviews_skipped']}")
        logger.info(f"Ошибок: {self.stats['errors']}")
        logger.info("=" * 50)
        
        return self.stats


def main():
    """Основная функция для запуска ETL"""
    # Путь к данным (можно передать как аргумент командной строки)
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    else:
        # Используем путь из проекта
        data_path = "/Users/mishantique/Desktop/Projects/gazprombank_hachaton/data/raw/banki_ru"
    
    # URL базы данных (можно передать как переменную окружения)
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/gazprombank_reviews"
    )
    
    logger.info(f"Запуск ETL загрузки данных")
    logger.info(f"Путь к данным: {data_path}")
    logger.info(f"База данных: {database_url}")
    
    # Создание и запуск ETL
    etl = ReviewETL(database_url)
    stats = etl.load_all_json_files(data_path)
    
    # Возвращаем код выхода на основе результатов
    if stats['errors'] > 0:
        logger.error("ETL завершился с ошибками")
        sys.exit(1)
    else:
        logger.info("ETL успешно завершен")
        sys.exit(0)


if __name__ == "__main__":
    main()
