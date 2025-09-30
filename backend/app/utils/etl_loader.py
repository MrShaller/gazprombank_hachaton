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
from sqlalchemy.sql import func

from models import Base, Product, Review, ProductAspect
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
            'aspects_loaded': 0,
            'aspects_skipped': 0,
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
    
    def parse_review_date(self, date_str: str) -> datetime:
        """
        Парсинг даты отзыва из различных форматов
        """
        # Список поддерживаемых форматов
        formats = [
            '%d.%m.%Y %H:%M',  # 31.05.2025 20:59
            '%Y-%m-%d',        # 2025-05-02
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        logger.error(f"Не удалось распарсить дату отзыва: {date_str}")
        raise ValueError(f"Неподдерживаемый формат даты: {date_str}")
    
    def parse_parsed_at(self, date_str: str) -> datetime:
        """
        Парсинг даты парсинга из ISO формата
        """
        try:
            # Удаляем микросекунды, если они есть
            if '.' in date_str:
                date_str = date_str.split('.')[0]
            return datetime.fromisoformat(date_str.replace('T', ' '))
        except ValueError:
            logger.error(f"Не удалось распарсить дату парсинга: {date_str}")
            raise

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
            if field not in review_data:
                logger.warning(f"Отсутствует обязательное поле: {field} для отзыва {review_data.get('review_id', 'unknown')}")
                return False
            
            # Специальная проверка для review_text - не должен быть пустым
            if field == 'review_text' and (not review_data[field] or str(review_data[field]).strip() == ''):
                logger.warning(f"Пустое поле review_text для отзыва {review_data.get('review_id', 'unknown')}")
                return False
            
            # Обычная проверка для других полей
            if field != 'review_text' and not review_data[field]:
                logger.warning(f"Отсутствует обязательное поле: {field} для отзыва {review_data.get('review_id', 'unknown')}")
                return False
        
        # Проверка рейтинга
        rating = review_data.get('rating')
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            logger.warning(f"Некорректный рейтинг: {rating} для отзыва {review_data.get('review_id', 'unknown')}")
            return False
        
        # Проверка тональности
        tonality = review_data.get('tonality')
        allowed_tonalities = ['положительно', 'отрицательно', 'нейтрально']
        if tonality not in allowed_tonalities:
            logger.warning(f"Некорректная тональность: {tonality} для отзыва {review_data.get('review_id', 'unknown')}")
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
                    # Получение или создание продукта (делаем ДО валидации)
                    product = self.get_or_create_product(session, review_data['product_type'])
                    
                    # Валидация данных
                    if not self.validate_review_data(review_data):
                        self.stats['reviews_skipped'] += 1
                        continue
                    
                    # Парсинг дат
                    review_date = self.parse_review_date(review_data['review_date'])
                    parsed_at = self.parse_parsed_at(review_data['parsed_at'])
                    
                    # Создаем уникальный ID для отзыва, включающий тип продукта
                    unique_review_id = f"{review_data['product_type']}_{review_data['review_id']}"
                    
                    # Проверка на дубликат по уникальному review_id
                    existing_review = session.query(Review).filter(
                        Review.review_id == unique_review_id
                    ).first()
                    
                    if existing_review:
                        self.stats['reviews_skipped'] += 1
                        logger.debug(f"Пропущен дубликат отзыва {unique_review_id}")
                        continue
                    
                    # Создание отзыва
                    review = Review(
                        review_id=unique_review_id,
                        product_id=product.id,
                        review_text=review_data['review_text'],
                        review_date=review_date,
                        url=review_data.get('url'),
                        parsed_at=parsed_at,
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
        logger.info(f"Аспектов загружено: {self.stats['aspects_loaded']}")
        logger.info(f"Аспектов пропущено: {self.stats['aspects_skipped']}")
        logger.info(f"Ошибок: {self.stats['errors']}")
        logger.info("=" * 50)
        
        return self.stats
    
    def load_aspects_from_json(self, json_file_path: str) -> int:
        """
        Загрузка анализа аспектов продуктов из JSON файла
        
        Args:
            json_file_path: Путь к JSON файлу с анализом аспектов
            
        Returns:
            int: Количество загруженных аспектов
        """
        logger.info(f"Загрузка анализа аспектов из файла: {json_file_path}")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                aspects_data = json.load(file)
        except Exception as e:
            logger.error(f"Ошибка чтения файла {json_file_path}: {e}")
            self.stats['errors'] += 1
            return 0
        
        if 'product_type' not in aspects_data:
            logger.error(f"Файл {json_file_path} не содержит ключ 'product_type'")
            self.stats['errors'] += 1
            return 0
        
        loaded_count = 0
        session = self.SessionLocal()
        
        try:
            for product_name, product_aspects in aspects_data['product_type'].items():
                try:
                    # Получаем продукт по имени
                    product = session.query(Product).filter(Product.name == product_name).first()
                    
                    if not product:
                        logger.warning(f"Продукт '{product_name}' не найден в базе данных. Пропускаем.")
                        self.stats['aspects_skipped'] += 1
                        continue
                    
                    # Удаляем существующие аспекты для этого продукта
                    existing_aspects = session.query(ProductAspect).filter(
                        ProductAspect.product_id == product.id
                    ).all()
                    
                    for aspect in existing_aspects:
                        session.delete(aspect)
                    
                    # Вычисляем среднюю оценку для продукта
                    avg_rating_query = session.query(func.avg(Review.rating)).filter(
                        Review.product_id == product.id
                    ).scalar()
                    avg_rating = float(avg_rating_query) if avg_rating_query else None
                    
                    # Загружаем плюсы
                    for pros_text in product_aspects.get('pros', []):
                        if pros_text.strip():
                            aspect = ProductAspect(
                                product_id=product.id,
                                aspect_type='pros',
                                aspect_text=pros_text.strip(),
                                avg_rating=avg_rating
                            )
                            session.add(aspect)
                            loaded_count += 1
                            self.stats['aspects_loaded'] += 1
                    
                    # Загружаем минусы
                    for cons_text in product_aspects.get('cons', []):
                        if cons_text.strip():
                            aspect = ProductAspect(
                                product_id=product.id,
                                aspect_type='cons',
                                aspect_text=cons_text.strip(),
                                avg_rating=avg_rating
                            )
                            session.add(aspect)
                            loaded_count += 1
                            self.stats['aspects_loaded'] += 1
                    
                    logger.info(f"Загружены аспекты для продукта '{product_name}': "
                              f"{len(product_aspects.get('pros', []))} плюсов, "
                              f"{len(product_aspects.get('cons', []))} минусов")
                
                except Exception as e:
                    logger.error(f"Ошибка обработки аспектов для продукта {product_name}: {e}")
                    self.stats['errors'] += 1
                    session.rollback()
            
            # Финальный коммит
            session.commit()
            logger.info(f"Завершена загрузка аспектов: {loaded_count} записей")
            
        except Exception as e:
            logger.error(f"Критическая ошибка при загрузке аспектов из {json_file_path}: {e}")
            session.rollback()
            self.stats['errors'] += 1
            
        finally:
            session.close()
        
        return loaded_count


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
