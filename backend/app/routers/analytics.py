"""
API роутеры для аналитики отзывов
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..crud import AnalyticsCRUD

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def get_summary_stats(db: Session = Depends(get_db)):
    """
    Получить общую сводную статистику по всем отзывам
    
    Возвращает:
    - Общее количество отзывов и продуктов
    - Средний рейтинг
    - Распределение по тональностям
    - Временные рамки данных
    """
    stats = AnalyticsCRUD.get_summary_stats(db)
    return stats


@router.get("/tonality")
def get_tonality_distribution(
    product_id: Optional[int] = Query(None, description="Фильтр по ID продукта"),
    start_date: Optional[datetime] = Query(None, description="Начальная дата"),
    end_date: Optional[datetime] = Query(None, description="Конечная дата"),
    db: Session = Depends(get_db)
):
    """
    Получить распределение отзывов по тональностям
    
    Возвращает:
    - Количество отзывов для каждой тональности
    - Процентное распределение
    - Средний рейтинг для каждой тональности
    
    Фильтры:
    - **product_id**: анализ только для конкретного продукта
    - **start_date**: начальная дата периода
    - **end_date**: конечная дата периода
    """
    distribution = AnalyticsCRUD.get_tonality_distribution(
        db=db,
        product_id=product_id,
        start_date=start_date,
        end_date=end_date
    )
    
    if not distribution:
        return {
            "distribution": [],
            "total_reviews": 0,
            "message": "Нет данных для указанных фильтров",
            "filters": {
                "product_id": product_id,
                "start_date": start_date,
                "end_date": end_date
            }
        }
    
    total_reviews = sum(item['count'] for item in distribution)
    
    return {
        "distribution": distribution,
        "total_reviews": total_reviews,
        "filters": {
            "product_id": product_id,
            "start_date": start_date,
            "end_date": end_date
        }
    }


@router.get("/dynamics")
def get_tonality_dynamics(
    product_id: Optional[int] = Query(None, description="Фильтр по ID продукта"),
    start_date: Optional[datetime] = Query(None, description="Начальная дата"),
    end_date: Optional[datetime] = Query(None, description="Конечная дата"),
    interval: str = Query("month", description="Интервал группировки: day, week, month"),
    db: Session = Depends(get_db)
):
    """
    Получить динамику изменения тональностей по времени
    
    Возвращает временной ряд с количеством и процентным распределением 
    отзывов по тональностям для каждого периода.
    
    Параметры:
    - **interval**: интервал группировки (day, week, month)
    - **product_id**: анализ только для конкретного продукта
    - **start_date**: начальная дата периода
    - **end_date**: конечная дата периода
    """
    if interval not in ['day', 'week', 'month']:
        raise HTTPException(
            status_code=400,
            detail="Интервал должен быть одним из: day, week, month"
        )
    
    dynamics = AnalyticsCRUD.get_tonality_dynamics(
        db=db,
        product_id=product_id,
        start_date=start_date,
        end_date=end_date,
        interval=interval
    )
    
    if not dynamics:
        return {
            "dynamics": [],
            "message": "Нет данных для указанных фильтров"
        }
    
    total_periods = len(dynamics)
    total_reviews = sum(item['total_count'] for item in dynamics)
    
    return {
        "dynamics": dynamics,
        "total_periods": total_periods,
        "total_reviews": total_reviews,
        "interval": interval,
        "filters": {
            "product_id": product_id,
            "start_date": start_date,
            "end_date": end_date
        }
    }


@router.get("/ratings")
def get_rating_distribution(
    product_id: Optional[int] = Query(None, description="Фильтр по ID продукта"),
    start_date: Optional[datetime] = Query(None, description="Начальная дата"),
    end_date: Optional[datetime] = Query(None, description="Конечная дата"),
    db: Session = Depends(get_db)
):
    """
    Получить распределение отзывов по рейтингам (1-5 звезд)
    
    Возвращает:
    - Количество отзывов для каждого рейтинга
    - Процентное распределение
    """
    distribution = AnalyticsCRUD.get_rating_distribution(
        db=db,
        product_id=product_id,
        start_date=start_date,
        end_date=end_date
    )
    
    if not distribution:
        return {
            "distribution": [],
            "message": "Нет данных для указанных фильтров"
        }
    
    total_reviews = sum(item['count'] for item in distribution)
    avg_rating = sum(item['rating'] * item['count'] for item in distribution) / total_reviews
    
    return {
        "distribution": distribution,
        "total_reviews": total_reviews,
        "average_rating": round(avg_rating, 2),
        "filters": {
            "product_id": product_id,
            "start_date": start_date,
            "end_date": end_date
        }
    }


@router.get("/top-reviews")
def get_top_reviews(
    product_id: Optional[int] = Query(None, description="Фильтр по ID продукта"),
    tonality: Optional[str] = Query(None, description="Фильтр по тональности"),
    limit: int = Query(10, ge=1, le=50, description="Количество отзывов"),
    db: Session = Depends(get_db)
):
    """
    Получить топ отзывы (отсортированные по рейтингу и дате)
    
    Параметры:
    - **product_id**: фильтр по продукту
    - **tonality**: фильтр по тональности
    - **limit**: количество отзывов в результате (1-50)
    """
    if tonality and tonality not in ['положительно', 'отрицательно', 'нейтрально']:
        raise HTTPException(
            status_code=400,
            detail="Тональность должна быть одной из: положительно, отрицательно, нейтрально"
        )
    
    reviews = AnalyticsCRUD.get_top_reviews(
        db=db,
        product_id=product_id,
        tonality=tonality,
        limit=limit
    )
    
    return {
        "reviews": reviews,
        "count": len(reviews),
        "filters": {
            "product_id": product_id,
            "tonality": tonality,
            "limit": limit
        }
    }
