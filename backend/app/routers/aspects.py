"""
API роутер для анализа аспектов продуктов
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..crud import AspectsCRUD
from ..schemas import ProductAspectsResponse, ProductsAspectsResponse

router = APIRouter(prefix="/aspects", tags=["aspects"])


@router.get("/product/{product_id}", response_model=ProductAspectsResponse)
def get_product_aspects(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить анализ аспектов для конкретного продукта
    
    Args:
        product_id: ID продукта
        db: Сессия базы данных
        
    Returns:
        Анализ аспектов продукта (плюсы и минусы)
    """
    aspects_data = AspectsCRUD.get_product_aspects(db, product_id)
    
    if not aspects_data:
        raise HTTPException(
            status_code=404,
            detail=f"Продукт с ID {product_id} не найден или не имеет анализа аспектов"
        )
    
    return ProductAspectsResponse(**aspects_data)


@router.get("/products", response_model=ProductsAspectsResponse)
def get_multiple_products_aspects(
    product_ids: Optional[str] = Query(None, description="ID продуктов через запятую"),
    db: Session = Depends(get_db)
):
    """
    Получить анализ аспектов для нескольких продуктов
    
    Args:
        product_ids: Строка с ID продуктов через запятую (например: "1,2,3")
        db: Сессия базы данных
        
    Returns:
        Анализ аспектов для указанных продуктов
    """
    # Парсим product_ids
    parsed_product_ids = None
    if product_ids:
        try:
            parsed_product_ids = [int(id.strip()) for id in product_ids.split(',') if id.strip()]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Некорректный формат product_ids. Используйте числа через запятую"
            )
    
    # Получаем данные
    products_aspects = AspectsCRUD.get_multiple_products_aspects(db, parsed_product_ids)
    
    # Формируем ответ
    response_data = {
        'products': products_aspects,
        'total_products': len(products_aspects),
        'filters': {
            'product_ids': parsed_product_ids
        }
    }
    
    return ProductsAspectsResponse(**response_data)


@router.get("/all", response_model=ProductsAspectsResponse)
def get_all_products_aspects(
    db: Session = Depends(get_db)
):
    """
    Получить анализ аспектов для всех продуктов
    
    Args:
        db: Сессия базы данных
        
    Returns:
        Полный анализ аспектов всех продуктов
    """
    response_data = AspectsCRUD.get_all_products_aspects(db)
    return ProductsAspectsResponse(**response_data)
