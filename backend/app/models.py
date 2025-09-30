"""
SQLAlchemy модели для дашборда анализа отзывов Газпромбанка
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, CheckConstraint, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Product(Base):
    """Модель продуктов/услуг банка"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи с отзывами и аспектами
    reviews = relationship("Review", back_populates="product")
    aspects = relationship("ProductAspect", back_populates="product")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}')>"


class Review(Base):
    """Модель отзывов клиентов"""
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(String(50), unique=True, nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    review_text = Column(Text, nullable=False)
    review_date = Column(DateTime(timezone=True), nullable=False, index=True)
    url = Column(String(500))
    parsed_at = Column(DateTime(timezone=True), nullable=False)
    bank_name = Column(String(50), nullable=False)
    rating = Column(Integer, nullable=False)
    tonality = Column(String(20), nullable=False, index=True)
    validation = Column(String(100))
    is_valid = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Ограничения
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
        CheckConstraint(
            "tonality IN ('положительно', 'отрицательно', 'нейтрально')", 
            name='check_tonality_values'
        ),
    )
    
    # Связь с продуктом
    product = relationship("Product", back_populates="reviews")
    
    def __repr__(self):
        return f"<Review(id={self.id}, review_id='{self.review_id}', tonality='{self.tonality}')>"


class ReviewStats(Base):
    """Предварительно агрегированная статистика для быстрых запросов"""
    __tablename__ = "review_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)  # Дата агрегации (день/месяц)
    tonality = Column(String(20), nullable=False, index=True)
    count = Column(Integer, nullable=False, default=0)
    avg_rating = Column(Integer, nullable=True)  # Средний рейтинг для данной тональности
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Ограничения
    __table_args__ = (
        CheckConstraint(
            "tonality IN ('положительно', 'отрицательно', 'нейтрально')", 
            name='check_stats_tonality_values'
        ),
    )
    
    # Связь с продуктом
    product = relationship("Product")
    
    def __repr__(self):
        return f"<ReviewStats(product_id={self.product_id}, date={self.date}, tonality='{self.tonality}', count={self.count})>"


class ProductAspect(Base):
    """Модель анализа аспектов продуктов (плюсы и минусы)"""
    __tablename__ = "product_aspects"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    aspect_type = Column(String(10), nullable=False, index=True)  # 'pros' или 'cons'
    aspect_text = Column(String(500), nullable=False)
    avg_rating = Column(Float, nullable=True)  # Средняя оценка для продукта
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Ограничения
    __table_args__ = (
        CheckConstraint(
            "aspect_type IN ('pros', 'cons')", 
            name='check_aspect_type_values'
        ),
    )
    
    # Связь с продуктом
    product = relationship("Product", back_populates="aspects")
    
    def __repr__(self):
        return f"<ProductAspect(product_id={self.product_id}, type='{self.aspect_type}', text='{self.aspect_text[:50]}...')>"
