"""
Pydantic схемы для валидации и сериализации данных
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator


class ProductBase(BaseModel):
    """Базовая схема продукта"""
    name: str = Field(..., max_length=100, description="Название продукта/услуги")


class ProductCreate(ProductBase):
    """Схема для создания продукта"""
    pass


class Product(ProductBase):
    """Схема продукта с полными данными"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReviewBase(BaseModel):
    """Базовая схема отзыва"""
    review_id: str = Field(..., max_length=50, description="Уникальный ID отзыва")
    review_text: str = Field(..., description="Текст отзыва")
    review_date: datetime = Field(..., description="Дата отзыва")
    url: Optional[str] = Field(None, max_length=500, description="URL отзыва")
    parsed_at: datetime = Field(..., description="Время парсинга")
    bank_name: str = Field(..., max_length=50, description="Название банка")
    rating: int = Field(..., ge=1, le=5, description="Рейтинг от 1 до 5")
    tonality: str = Field(..., description="Тональность отзыва")
    validation: Optional[str] = Field(None, max_length=100, description="Статус валидации")
    is_valid: bool = Field(True, description="Валидность отзыва")
    
    @validator('tonality')
    def validate_tonality(cls, v):
        """Валидация тональности"""
        allowed_values = ['положительно', 'отрицательно', 'нейтрально']
        if v not in allowed_values:
            raise ValueError(f'Тональность должна быть одной из: {allowed_values}')
        return v


class ReviewCreate(ReviewBase):
    """Схема для создания отзыва"""
    product_id: int = Field(..., description="ID продукта")


class Review(ReviewBase):
    """Схема отзыва с полными данными"""
    id: int
    product_id: int
    created_at: datetime
    product: Product
    
    class Config:
        from_attributes = True


class TonalityStats(BaseModel):
    """Схема статистики по тональности"""
    tonality: str = Field(..., description="Тональность")
    count: int = Field(..., description="Количество отзывов")
    percentage: float = Field(..., description="Процент от общего числа отзывов")
    avg_rating: Optional[float] = Field(None, description="Средний рейтинг")


class ProductTonalityStats(BaseModel):
    """Схема статистики по продукту"""
    product: Product
    total_reviews: int = Field(..., description="Общее количество отзывов")
    tonality_distribution: List[TonalityStats] = Field(..., description="Распределение по тональностям")


class TimeSeriesPoint(BaseModel):
    """Точка временного ряда"""
    date: datetime = Field(..., description="Дата")
    tonality: str = Field(..., description="Тональность")
    count: int = Field(..., description="Количество отзывов")
    percentage: float = Field(..., description="Процент от общего числа")


class ProductDynamics(BaseModel):
    """Схема динамики продукта по времени"""
    product: Product
    time_series: List[TimeSeriesPoint] = Field(..., description="Временной ряд")


class DateFilter(BaseModel):
    """Фильтр по датам"""
    start_date: Optional[datetime] = Field(None, description="Начальная дата")
    end_date: Optional[datetime] = Field(None, description="Конечная дата")


class AnalyticsQuery(BaseModel):
    """Запрос для аналитики"""
    product_ids: Optional[List[int]] = Field(None, description="ID продуктов для фильтрации")
    date_filter: Optional[DateFilter] = Field(None, description="Фильтр по датам")
    tonality: Optional[str] = Field(None, description="Фильтр по тональности")
    
    @validator('tonality')
    def validate_tonality_filter(cls, v):
        """Валидация фильтра тональности"""
        if v is not None:
            allowed_values = ['положительно', 'отрицательно', 'нейтрально']
            if v not in allowed_values:
                raise ValueError(f'Тональность должна быть одной из: {allowed_values}')
        return v


# Схемы для обработки загрузки файлов

class FileUploadItem(BaseModel):
    """Элемент данных в загружаемом файле"""
    id: Union[int, str] = Field(..., description="Уникальный идентификатор записи")
    text: str = Field(..., min_length=1, description="Текст для анализа")

class FileUploadData(BaseModel):
    """Структура данных загружаемого файла"""
    data: List[FileUploadItem] = Field(..., min_items=1, description="Массив данных для обработки")

class PredictionItem(BaseModel):
    """Элемент предсказания"""
    id: Union[int, str] = Field(..., description="ID записи")
    topics: List[str] = Field(..., description="Список определенных тем/продуктов")
    sentiments: List[str] = Field(..., description="Список тональностей для каждой темы")

class PredictResponse(BaseModel):
    """Ответ сервиса предсказаний"""
    predictions: List[PredictionItem] = Field(..., description="Список предсказаний")

class ErrorResponse(BaseModel):
    """Ответ с ошибкой"""
    success: bool = Field(False, description="Статус выполнения операции")
    message: str = Field(..., description="Сообщение об ошибке")
    error_code: Optional[str] = Field(None, description="Код ошибки")
    details: Optional[Dict[str, Any]] = Field(None, description="Дополнительные детали ошибки")


# Схемы для анализа аспектов продуктов

class ProductAspectBase(BaseModel):
    """Базовая схема аспекта продукта"""
    aspect_type: str = Field(..., description="Тип аспекта: 'pros' или 'cons'")
    aspect_text: str = Field(..., max_length=500, description="Текст аспекта")
    avg_rating: Optional[float] = Field(None, description="Средняя оценка продукта")


class ProductAspectCreate(ProductAspectBase):
    """Схема для создания аспекта продукта"""
    product_id: int = Field(..., description="ID продукта")


class ProductAspect(ProductAspectBase):
    """Схема аспекта продукта с полными данными"""
    id: int
    product_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProductAspectsResponse(BaseModel):
    """Ответ с анализом аспектов продукта"""
    product_id: int = Field(..., description="ID продукта")
    product_name: str = Field(..., description="Название продукта")
    avg_rating: Optional[float] = Field(None, description="Средняя оценка продукта")
    pros: List[str] = Field(default_factory=list, description="Список преимуществ")
    cons: List[str] = Field(default_factory=list, description="Список недостатков")
    total_aspects: int = Field(..., description="Общее количество аспектов")


class ProductsAspectsResponse(BaseModel):
    """Ответ с анализом аспектов для нескольких продуктов"""
    products: List[ProductAspectsResponse] = Field(..., description="Список продуктов с анализом аспектов")
    total_products: int = Field(..., description="Общее количество продуктов")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Примененные фильтры")
