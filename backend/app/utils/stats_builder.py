"""
Построение предварительно агрегированной статистики для быстрых запросов
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List
import logging
from sqlalchemy import func, create_engine
from sqlalchemy.orm import sessionmaker

# Добавляем путь к модулям приложения
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Review, Product, ReviewStats
from config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StatsBuilder:
    """Класс для построения агрегированной статистики"""
    
    def __init__(self, database_url: str = None):
        """
        Инициализация построителя статистики
        
        Args:
            database_url: URL подключения к БД
        """
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def build_daily_stats(self) -> Dict:
        """
        Построение ежедневной статистики по продуктам и тональностям
        
        Returns:
            Dict: Статистика построения
        """
        logger.info("Начало построения ежедневной статистики...")
        
        session = self.SessionLocal()
        stats = {'records_created': 0, 'records_updated': 0, 'errors': 0}
        
        try:
            # Очистка существующей статистики
            session.query(ReviewStats).delete()
            session.commit()
            
            # Получение всех комбинаций продукт-дата-тональность
            query = session.query(
                Review.product_id,
                func.date(Review.review_date).label('review_date'),
                Review.tonality,
                func.count().label('count'),
                func.avg(Review.rating).label('avg_rating')
            ).filter(
                Review.is_valid == True
            ).group_by(
                Review.product_id,
                func.date(Review.review_date),
                Review.tonality
            )
            
            results = query.all()
            logger.info(f"Найдено {len(results)} уникальных комбинаций для статистики")
            
            # Создание записей статистики
            for result in results:
                try:
                    stat_record = ReviewStats(
                        product_id=result.product_id,
                        date=datetime.combine(result.review_date, datetime.min.time()),
                        tonality=result.tonality,
                        count=result.count,
                        avg_rating=round(result.avg_rating, 2) if result.avg_rating else None
                    )
                    
                    session.add(stat_record)
                    stats['records_created'] += 1
                    
                    # Коммит каждые 100 записей
                    if stats['records_created'] % 100 == 0:
                        session.commit()
                        logger.info(f"Создано {stats['records_created']} записей статистики")
                
                except Exception as e:
                    logger.error(f"Ошибка создания статистики: {e}")
                    stats['errors'] += 1
                    session.rollback()
            
            # Финальный коммит
            session.commit()
            logger.info(f"Построение статистики завершено: {stats['records_created']} записей")
            
        except Exception as e:
            logger.error(f"Критическая ошибка при построении статистики: {e}")
            session.rollback()
            stats['errors'] += 1
            
        finally:
            session.close()
        
        return stats
    
    def get_products_summary(self) -> List[Dict]:
        """
        Получение сводки по продуктам
        
        Returns:
            List[Dict]: Список продуктов с количеством отзывов
        """
        session = self.SessionLocal()
        
        try:
            query = session.query(
                Product.id,
                Product.name,
                func.count(Review.id).label('total_reviews'),
                func.count(func.nullif(Review.tonality == 'положительно', False)).label('positive'),
                func.count(func.nullif(Review.tonality == 'отрицательно', False)).label('negative'),
                func.count(func.nullif(Review.tonality == 'нейтрально', False)).label('neutral'),
                func.avg(Review.rating).label('avg_rating')
            ).outerjoin(Review).group_by(Product.id, Product.name)
            
            results = query.all()
            
            summary = []
            for result in results:
                summary.append({
                    'product_id': result.id,
                    'product_name': result.name,
                    'total_reviews': result.total_reviews,
                    'positive_reviews': result.positive or 0,
                    'negative_reviews': result.negative or 0,
                    'neutral_reviews': result.neutral or 0,
                    'avg_rating': round(result.avg_rating, 2) if result.avg_rating else None
                })
            
            return summary
            
        finally:
            session.close()
    
    def print_summary(self):
        """Вывод сводки по данным"""
        logger.info("=" * 60)
        logger.info("СВОДКА ПО ЗАГРУЖЕННЫМ ДАННЫМ")
        logger.info("=" * 60)
        
        summary = self.get_products_summary()
        
        total_reviews = sum(item['total_reviews'] for item in summary)
        total_positive = sum(item['positive_reviews'] for item in summary)
        total_negative = sum(item['negative_reviews'] for item in summary)
        total_neutral = sum(item['neutral_reviews'] for item in summary)
        
        logger.info(f"Общая статистика:")
        logger.info(f"  Всего продуктов: {len(summary)}")
        logger.info(f"  Всего отзывов: {total_reviews}")
        logger.info(f"  Положительных: {total_positive} ({total_positive/total_reviews*100:.1f}%)")
        logger.info(f"  Отрицательных: {total_negative} ({total_negative/total_reviews*100:.1f}%)")
        logger.info(f"  Нейтральных: {total_neutral} ({total_neutral/total_reviews*100:.1f}%)")
        
        logger.info("\nПо продуктам:")
        for item in sorted(summary, key=lambda x: x['total_reviews'], reverse=True):
            if item['total_reviews'] > 0:
                pos_pct = item['positive_reviews'] / item['total_reviews'] * 100
                neg_pct = item['negative_reviews'] / item['total_reviews'] * 100
                logger.info(f"  {item['product_name']}: {item['total_reviews']} отзывов "
                          f"(+{pos_pct:.1f}%, -{neg_pct:.1f}%, ★{item['avg_rating']})")
        
        logger.info("=" * 60)


def main():
    """Основная функция для построения статистики"""
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/gazprombank_reviews"
    )
    
    logger.info("Запуск построения статистики")
    
    builder = StatsBuilder(database_url)
    
    # Построение статистики
    stats = builder.build_daily_stats()
    
    # Вывод сводки
    builder.print_summary()
    
    if stats['errors'] > 0:
        logger.error("Построение статистики завершилось с ошибками")
        sys.exit(1)
    else:
        logger.info("Построение статистики успешно завершено")
        sys.exit(0)


if __name__ == "__main__":
    main()
