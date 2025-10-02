"""
API роутеры для работы с продуктами
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..crud import ProductCRUD
from ..schemas import Product, ProductCreate

router = APIRouter(tags=["products"])

@router.get("/", response_model=List[Product])
def get_products(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    db: Session = Depends(get_db)
):
    """
    Получить список всех продуктов/услуг
    
    - **skip**: количество записей для пропуска (для пагинации)
    - **limit**: максимальное количество записей в ответе
    """
    products = ProductCRUD.get_all(db, skip=skip, limit=limit)
    return products


@router.get("/stats")
def get_products_with_stats(db: Session = Depends(get_db)):
    """
    Получить список продуктов с базовой статистикой
    
    Возвращает:
    - Общее количество отзывов по каждому продукту
    - Распределение по тональностям (количество и проценты)
    - Средний рейтинг
    - Даты первого и последнего отзыва
    """
    products_stats = ProductCRUD.get_products_with_stats(db)
    return {
        "products": products_stats,
        "total_products": len(products_stats),
        "products_with_reviews": len([p for p in products_stats if p['total_reviews'] > 0])
    }


@router.get("/{product_id}", response_model=Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Получить продукт по ID
    
    - **product_id**: уникальный идентификатор продукта
    """
    product = ProductCRUD.get_by_id(db, product_id=product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    return product


@router.post("/", response_model=Product)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    Создать новый продукт
    
    - **name**: название продукта (должно быть уникальным)
    """
    # Проверка на существование продукта с таким именем
    existing_product = ProductCRUD.get_by_name(db, name=product.name)
    if existing_product:
        raise HTTPException(
            status_code=400, 
            detail=f"Продукт с названием '{product.name}' уже существует"
        )
    
    return ProductCRUD.create(db=db, product=product)
