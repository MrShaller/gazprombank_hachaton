"""
API роутеры для работы с отзывами
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..crud import ReviewCRUD
from ..schemas import Review

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/", response_model=List[Review])
def get_reviews(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(50, ge=1, le=100, description="Максимальное количество записей"),
    product_id: Optional[int] = Query(None, description="Фильтр по ID продукта"),
    tonality: Optional[str] = Query(None, description="Фильтр по тональности"),
    start_date: Optional[datetime] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    end_date: Optional[datetime] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Получить список отзывов с фильтрацией
    
    Поддерживаемые фильтры:
    - **product_id**: фильтр по продукту
    - **tonality**: фильтр по тональности (положительно/отрицательно/нейтрально)
    - **start_date**: начальная дата в формате YYYY-MM-DD
    - **end_date**: конечная дата в формате YYYY-MM-DD
    """
    # Валидация тональности
    if tonality and tonality not in ['положительно', 'отрицательно', 'нейтрально']:
        raise HTTPException(
            status_code=400,
            detail="Тональность должна быть одной из: положительно, отрицательно, нейтрально"
        )
    
    reviews = ReviewCRUD.get_all(
        db=db,
        skip=skip,
        limit=limit,
        product_id=product_id,
        tonality=tonality,
        start_date=start_date,
        end_date=end_date
    )
    
    # Получение общего количества для пагинации
    total_count = ReviewCRUD.get_count(
        db=db,
        product_id=product_id,
        tonality=tonality,
        start_date=start_date,
        end_date=end_date
    )
    
    return reviews


@router.get("/count")
def get_reviews_count(
    product_id: Optional[int] = Query(None, description="Фильтр по ID продукта"),
    tonality: Optional[str] = Query(None, description="Фильтр по тональности"),
    start_date: Optional[datetime] = Query(None, description="Начальная дата"),
    end_date: Optional[datetime] = Query(None, description="Конечная дата"),
    db: Session = Depends(get_db)
):
    """
    Получить количество отзывов с фильтрацией
    
    Возвращает общее количество отзывов, соответствующих заданным фильтрам.
    """
    if tonality and tonality not in ['положительно', 'отрицательно', 'нейтрально']:
        raise HTTPException(
            status_code=400,
            detail="Тональность должна быть одной из: положительно, отрицательно, нейтрально"
        )
    
    count = ReviewCRUD.get_count(
        db=db,
        product_id=product_id,
        tonality=tonality,
        start_date=start_date,
        end_date=end_date
    )
    
    return {"count": count}


@router.get("/{review_id}", response_model=Review)
def get_review(review_id: int, db: Session = Depends(get_db)):
    """
    Получить отзыв по ID
    
    - **review_id**: уникальный идентификатор отзыва
    """
    review = ReviewCRUD.get_by_id(db, review_id=review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    return review
