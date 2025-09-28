/**
 * Список продуктов с горизонтальными барами тональностей
 */
'use client';

import { ChevronRight } from 'lucide-react';
import { getTonalityColor, formatPercent, formatNumber } from '@/lib/utils';
import type { ProductStats } from '@/types/api';

interface ProductsListProps {
  products: ProductStats[];
  onProductSelect?: (productId: number) => void;
  onProductsSelect?: (productIds: number[]) => void;
  selectedProductId?: number;
  selectedProductIds?: number[];
  className?: string;
  showAll?: boolean;
  maxItems?: number;
}

export default function ProductsList({
  products,
  onProductSelect,
  onProductsSelect,
  selectedProductId,
  selectedProductIds = [],
  className = '',
  showAll = false,
  maxItems = 10,
}: ProductsListProps) {
  // Фильтруем продукты с отзывами и сортируем по количеству
  const filteredProducts = products
    .filter(product => product.total_reviews > 0)
    .sort((a, b) => b.total_reviews - a.total_reviews);

  // Функция для переключения выбора продукта
  const toggleProduct = (productId: number) => {
    if (onProductsSelect) {
      const newSelectedIds = selectedProductIds.includes(productId)
        ? selectedProductIds.filter(id => id !== productId) // Убираем если уже выбран
        : [...selectedProductIds, productId]; // Добавляем если не выбран
      
      onProductsSelect(newSelectedIds);
    } else if (onProductSelect) {
      // Обратная совместимость с одиночным выбором
      onProductSelect(productId);
    }
  };

  // Ограничиваем количество отображаемых продуктов
  const displayProducts = showAll ? filteredProducts : filteredProducts.slice(0, maxItems);

  const ProductBar = ({ product }: { product: ProductStats }) => {
    const isSelected = selectedProductIds.includes(product.id) || selectedProductId === product.id;
    
    return (
      <div
        className={`
          group relative bg-gazprom-blue rounded-lg p-4 cursor-pointer transition-all duration-200
          ${isSelected ? 'ring-2 ring-gazprom-blue-light shadow-lg' : 'hover:shadow-md hover:bg-gazprom-blue-dark'}
        `}
        onClick={() => toggleProduct(product.id)}
      >
        {/* Заголовок продукта */}
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-white font-medium text-sm truncate pr-2">
            {product.name}
          </h4>
          <div className="flex items-center space-x-2 text-white">
            <span className="text-sm font-bold">
              {formatNumber(product.total_reviews)}
            </span>
            {onProductSelect && (
              <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            )}
          </div>
        </div>

        {/* Горизонтальная полоса тональностей */}
        <div className="relative">
          <div className="flex h-6 rounded-full overflow-hidden bg-white/20">
            {/* Положительная тональность */}
            {product.positive_percentage > 0 && (
              <div
                className="bg-sentiment-positive flex items-center justify-center text-xs font-medium text-white"
                style={{ width: `${product.positive_percentage}%` }}
                title={`Положительные: ${formatPercent(product.positive_percentage)} (${formatNumber(product.positive_reviews)})`}
              >
                {product.positive_percentage >= 15 && (
                  <span>{formatPercent(product.positive_percentage, 0)}</span>
                )}
              </div>
            )}

            {/* Нейтральная тональность */}
            {product.neutral_percentage > 0 && (
              <div
                className="bg-sentiment-neutral flex items-center justify-center text-xs font-medium text-white"
                style={{ width: `${product.neutral_percentage}%` }}
                title={`Нейтральные: ${formatPercent(product.neutral_percentage)} (${formatNumber(product.neutral_reviews)})`}
              >
                {product.neutral_percentage >= 15 && (
                  <span>{formatPercent(product.neutral_percentage, 0)}</span>
                )}
              </div>
            )}

            {/* Отрицательная тональность */}
            {product.negative_percentage > 0 && (
              <div
                className="bg-sentiment-negative flex items-center justify-center text-xs font-medium text-white"
                style={{ width: `${product.negative_percentage}%` }}
                title={`Отрицательные: ${formatPercent(product.negative_percentage)} (${formatNumber(product.negative_reviews)})`}
              >
                {product.negative_percentage >= 15 && (
                  <span>{formatPercent(product.negative_percentage, 0)}</span>
                )}
              </div>
            )}
          </div>

          {/* Детальная информация при наведении */}
          <div className="absolute top-8 left-0 right-0 bg-black/80 text-white text-xs rounded p-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10">
            <div className="flex justify-between items-center space-x-4">
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 rounded-full bg-sentiment-positive"></div>
                <span>Позитив: {formatNumber(product.positive_reviews)}</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 rounded-full bg-sentiment-neutral"></div>
                <span>Нейтр: {formatNumber(product.neutral_reviews)}</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 rounded-full bg-sentiment-negative"></div>
                <span>Негатив: {formatNumber(product.negative_reviews)}</span>
              </div>
            </div>
            {product.avg_rating && (
              <div className="mt-1 text-center">
                Средний рейтинг: ★ {product.avg_rating.toFixed(1)}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className={`bg-white rounded-lg p-6 ${className}`}>
      {/* Заголовок */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Все продукты/услуги
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Видим кол-во отзывов и соотношение тональностей
          </p>
        </div>
        
        {!showAll && filteredProducts.length > maxItems && (
          <button className="text-gazprom-blue hover:text-gazprom-blue-dark text-sm font-medium">
            Перелистнуть
          </button>
        )}
      </div>

      {/* Список продуктов */}
      <div className="space-y-3">
        {displayProducts.map((product) => (
          <ProductBar key={product.id} product={product} />
        ))}
      </div>

      {/* Сообщение о пустом списке */}
      {displayProducts.length === 0 && (
        <div className="text-center py-8">
          <div className="text-gray-500 text-sm">
            Нет продуктов с отзывами
          </div>
        </div>
      )}

      {/* Информация о скрытых элементах */}
      {!showAll && filteredProducts.length > maxItems && (
        <div className="mt-4 text-center">
          <p className="text-xs text-gray-500">
            Показано {displayProducts.length} из {filteredProducts.length} продуктов
          </p>
        </div>
      )}
    </div>
  );
}
