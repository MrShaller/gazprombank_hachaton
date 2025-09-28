"""
CRUD операции для работы с базой данных
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from sqlalchemy.sql import text

from .models import Product, Review, ReviewStats
from .schemas import ProductCreate, ReviewCreate, AnalyticsQuery


class ProductCRUD:
    """CRUD операции для продуктов"""
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
        """Получить все продукты с пагинацией"""
        return db.query(Product).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_id(db: Session, product_id: int) -> Optional[Product]:
        """Получить продукт по ID"""
        return db.query(Product).filter(Product.id == product_id).first()
    
    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Product]:
        """Получить продукт по названию"""
        return db.query(Product).filter(Product.name == name).first()
    
    @staticmethod
    def create(db: Session, product: ProductCreate) -> Product:
        """Создать новый продукт"""
        db_product = Product(name=product.name)
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    
    @staticmethod
    def get_products_with_stats(db: Session) -> List[Dict[str, Any]]:
        """Получить продукты с базовой статистикой"""
        query = db.query(
            Product.id,
            Product.name,
            func.count(Review.id).label('total_reviews'),
            func.count(func.nullif(Review.tonality == 'положительно', False)).label('positive'),
            func.count(func.nullif(Review.tonality == 'отрицательно', False)).label('negative'),
            func.count(func.nullif(Review.tonality == 'нейтрально', False)).label('neutral'),
            func.avg(Review.rating).label('avg_rating'),
            func.min(Review.review_date).label('first_review'),
            func.max(Review.review_date).label('last_review')
        ).outerjoin(Review).group_by(Product.id, Product.name).order_by(desc('total_reviews'))
        
        results = query.all()
        
        products_stats = []
        for result in results:
            total = result.total_reviews or 0
            products_stats.append({
                'id': result.id,
                'name': result.name,
                'total_reviews': total,
                'positive_reviews': result.positive or 0,
                'negative_reviews': result.negative or 0,
                'neutral_reviews': result.neutral or 0,
                'positive_percentage': round((result.positive or 0) / total * 100, 1) if total > 0 else 0,
                'negative_percentage': round((result.negative or 0) / total * 100, 1) if total > 0 else 0,
                'neutral_percentage': round((result.neutral or 0) / total * 100, 1) if total > 0 else 0,
                'avg_rating': round(result.avg_rating, 2) if result.avg_rating else None,
                'first_review': result.first_review,
                'last_review': result.last_review
            })
        
        return products_stats


class ReviewCRUD:
    """CRUD операции для отзывов"""
    
    @staticmethod
    def get_all(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        product_id: Optional[int] = None,
        tonality: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Review]:
        """Получить отзывы с фильтрацией"""
        query = db.query(Review)
        
        # Применение фильтров
        if product_id:
            query = query.filter(Review.product_id == product_id)
        if tonality:
            query = query.filter(Review.tonality == tonality)
        if start_date:
            query = query.filter(Review.review_date >= start_date)
        if end_date:
            query = query.filter(Review.review_date <= end_date)
        
        return query.order_by(desc(Review.review_date)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_id(db: Session, review_id: int) -> Optional[Review]:
        """Получить отзыв по ID"""
        return db.query(Review).filter(Review.id == review_id).first()
    
    @staticmethod
    def get_count(
        db: Session,
        product_id: Optional[int] = None,
        tonality: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Получить количество отзывов с фильтрацией"""
        query = db.query(func.count(Review.id))
        
        if product_id:
            query = query.filter(Review.product_id == product_id)
        if tonality:
            query = query.filter(Review.tonality == tonality)
        if start_date:
            query = query.filter(Review.review_date >= start_date)
        if end_date:
            query = query.filter(Review.review_date <= end_date)
        
        return query.scalar()


class AnalyticsCRUD:
    """CRUD операции для аналитики"""
    
    @staticmethod
    def get_tonality_distribution(
        db: Session,
        product_id: Optional[int] = None,
        product_ids: Optional[List[int]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Получить распределение по тональностям"""
        query = db.query(
            Review.tonality,
            func.count().label('count'),
            func.avg(Review.rating).label('avg_rating')
        ).filter(Review.is_valid == True)
        
        # Применение фильтров
        if product_ids and len(product_ids) > 0:
            query = query.filter(Review.product_id.in_(product_ids))
        elif product_id:
            query = query.filter(Review.product_id == product_id)
        if start_date:
            query = query.filter(Review.review_date >= start_date)
        if end_date:
            query = query.filter(Review.review_date <= end_date)
        
        results = query.group_by(Review.tonality).all()
        
        # Подсчет общего количества для процентов
        total_count = sum(result.count for result in results)
        
        distribution = []
        for result in results:
            distribution.append({
                'tonality': result.tonality,
                'count': result.count,
                'percentage': round(result.count / total_count * 100, 1) if total_count > 0 else 0,
                'avg_rating': round(result.avg_rating, 2) if result.avg_rating else None
            })
        
        return distribution
    
    @staticmethod
    def get_tonality_dynamics(
        db: Session,
        product_id: Optional[int] = None,
        product_ids: Optional[List[int]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = 'month'  # 'day', 'week', 'month'
    ) -> List[Dict[str, Any]]:
        """Получить динамику тональностей по времени"""
        
        # Определяем функцию группировки по интервалу
        if interval == 'day':
            date_trunc = func.date_trunc('day', Review.review_date)
        elif interval == 'week':
            date_trunc = func.date_trunc('week', Review.review_date)
        else:  # month
            date_trunc = func.date_trunc('month', Review.review_date)
        
        query = db.query(
            date_trunc.label('period'),
            Review.tonality,
            func.count().label('count')
        ).filter(Review.is_valid == True)
        
        # Применение фильтров
        if product_ids and len(product_ids) > 0:
            query = query.filter(Review.product_id.in_(product_ids))
        elif product_id:
            query = query.filter(Review.product_id == product_id)
        if start_date:
            query = query.filter(Review.review_date >= start_date)
        if end_date:
            query = query.filter(Review.review_date <= end_date)
        
        results = query.group_by('period', Review.tonality).order_by('period').all()
        
        # Группировка результатов по периодам
        dynamics = {}
        for result in results:
            period_str = result.period.strftime('%Y-%m-%d')
            if period_str not in dynamics:
                dynamics[period_str] = {
                    'date': result.period,
                    'положительно': 0,
                    'отрицательно': 0,
                    'нейтрально': 0,
                    'total': 0
                }
            
            dynamics[period_str][result.tonality] = result.count
            dynamics[period_str]['total'] += result.count
        
        # Преобразование в список с процентами
        dynamics_list = []
        for period_data in dynamics.values():
            total = period_data['total']
            dynamics_list.append({
                'date': period_data['date'],
                'positive_count': period_data['положительно'],
                'negative_count': period_data['отрицательно'],
                'neutral_count': period_data['нейтрально'],
                'total_count': total,
                'positive_percentage': round(period_data['положительно'] / total * 100, 1) if total > 0 else 0,
                'negative_percentage': round(period_data['отрицательно'] / total * 100, 1) if total > 0 else 0,
                'neutral_percentage': round(period_data['нейтрально'] / total * 100, 1) if total > 0 else 0
            })
        
        return sorted(dynamics_list, key=lambda x: x['date'])
    
    @staticmethod
    def get_rating_distribution(
        db: Session,
        product_id: Optional[int] = None,
        product_ids: Optional[List[int]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Получить распределение по рейтингам"""
        query = db.query(
            Review.rating,
            func.count().label('count')
        ).filter(Review.is_valid == True)
        
        # Применение фильтров
        if product_ids and len(product_ids) > 0:
            query = query.filter(Review.product_id.in_(product_ids))
        elif product_id:
            query = query.filter(Review.product_id == product_id)
        if start_date:
            query = query.filter(Review.review_date >= start_date)
        if end_date:
            query = query.filter(Review.review_date <= end_date)
        
        results = query.group_by(Review.rating).order_by(Review.rating).all()
        
        total_count = sum(result.count for result in results)
        
        distribution = []
        for result in results:
            distribution.append({
                'rating': result.rating,
                'count': result.count,
                'percentage': round(result.count / total_count * 100, 1) if total_count > 0 else 0
            })
        
        return distribution
    
    @staticmethod
    def get_top_reviews(
        db: Session,
        product_id: Optional[int] = None,
        tonality: Optional[str] = None,
        limit: int = 10
    ) -> List[Review]:
        """Получить топ отзывы (по рейтингу и дате)"""
        query = db.query(Review).filter(Review.is_valid == True)
        
        if product_id:
            query = query.filter(Review.product_id == product_id)
        if tonality:
            query = query.filter(Review.tonality == tonality)
        
        # Сортировка: сначала по рейтингу, потом по дате
        return query.order_by(desc(Review.rating), desc(Review.review_date)).limit(limit).all()
    
    @staticmethod
    def get_summary_stats(db: Session) -> Dict[str, Any]:
        """Получить общую сводную статистику"""
        # Общие показатели
        total_reviews = db.query(func.count(Review.id)).filter(Review.is_valid == True).scalar()
        total_products = db.query(func.count(Product.id)).scalar()
        avg_rating = db.query(func.avg(Review.rating)).filter(Review.is_valid == True).scalar()
        
        # Распределение по тональности
        tonality_stats = db.query(
            Review.tonality,
            func.count().label('count')
        ).filter(Review.is_valid == True).group_by(Review.tonality).all()
        
        tonality_dict = {stat.tonality: stat.count for stat in tonality_stats}
        
        # Временные рамки
        date_range = db.query(
            func.min(Review.review_date).label('first_review'),
            func.max(Review.review_date).label('last_review')
        ).filter(Review.is_valid == True).first()
        
        return {
            'total_reviews': total_reviews,
            'total_products': total_products,
            'avg_rating': round(avg_rating, 2) if avg_rating else None,
            'positive_reviews': tonality_dict.get('положительно', 0),
            'negative_reviews': tonality_dict.get('отрицательно', 0),
            'neutral_reviews': tonality_dict.get('нейтрально', 0),
            'first_review_date': date_range.first_review,
            'last_review_date': date_range.last_review,
            'positive_percentage': round(tonality_dict.get('положительно', 0) / total_reviews * 100, 1) if total_reviews > 0 else 0,
            'negative_percentage': round(tonality_dict.get('отрицательно', 0) / total_reviews * 100, 1) if total_reviews > 0 else 0,
            'neutral_percentage': round(tonality_dict.get('нейтрально', 0) / total_reviews * 100, 1) if total_reviews > 0 else 0
        }
