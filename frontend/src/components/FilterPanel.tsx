/**
 * Панель фильтров для дашборда
 */
'use client';

import { useState } from 'react';
import { Calendar, ChevronDown } from 'lucide-react';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import type { ProductStats, IntervalType } from '@/types/api';

interface FilterPanelProps {
  products: ProductStats[];
  selectedProductId?: number;
  selectedTonality?: string;
  startDate?: Date;
  endDate?: Date;
  interval?: IntervalType;
  onProductChange?: (productId?: number) => void;
  onTonalityChange?: (tonality?: string) => void;
  onDateRangeChange?: (startDate?: Date, endDate?: Date) => void;
  onIntervalChange?: (interval: IntervalType) => void;
  className?: string;
}

export default function FilterPanel({
  products,
  selectedProductId,
  selectedTonality,
  startDate,
  endDate,
  interval = 'month',
  onProductChange,
  onTonalityChange,
  onDateRangeChange,
  onIntervalChange,
  className = '',
}: FilterPanelProps) {
  const [isProductDropdownOpen, setIsProductDropdownOpen] = useState(false);
  const [isTonalityDropdownOpen, setIsTonalityDropdownOpen] = useState(false);

  // Опции тональности
  const tonalityOptions = [
    { value: undefined, label: 'Все' },
    { value: 'положительно', label: 'Положительная' },
    { value: 'нейтрально', label: 'Нейтральная' },
    { value: 'отрицательно', label: 'Отрицательная' },
  ];

  // Опции интервалов
  const intervalOptions = [
    { value: 'day' as IntervalType, label: 'День' },
    { value: 'week' as IntervalType, label: 'Неделя' },
    { value: 'month' as IntervalType, label: 'Месяц' },
  ];

  // Получаем название выбранного продукта
  const selectedProduct = products.find(p => p.id === selectedProductId);
  const selectedProductName = selectedProduct ? selectedProduct.name : 'Все';

  // Получаем название выбранной тональности
  const selectedTonalityOption = tonalityOptions.find(t => t.value === selectedTonality);
  const selectedTonalityName = selectedTonalityOption ? selectedTonalityOption.label : 'Все';

  // Форматирование диапазона дат
  const formatDateRange = () => {
    if (!startDate || !endDate) {
      return 'XX.XX.XXXX — XX.XX.XXXX';
    }
    
    const start = format(startDate, 'dd.MM.yyyy', { locale: ru });
    const end = format(endDate, 'dd.MM.yyyy', { locale: ru });
    return `${start} — ${end}`;
  };

  // Dropdown компонент
  const Dropdown = ({ 
    isOpen, 
    onToggle, 
    children, 
    trigger 
  }: { 
    isOpen: boolean; 
    onToggle: () => void; 
    children: React.ReactNode; 
    trigger: React.ReactNode; 
  }) => (
    <div className="relative">
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full px-4 py-2 text-left bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gazprom-blue"
      >
        {trigger}
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto">
          {children}
        </div>
      )}
    </div>
  );

  return (
    <div className={`bg-gray-50 p-6 rounded-lg ${className}`}>
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {/* Период */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Период
          </label>
          <div className="relative">
            <input
              type="text"
              value={formatDateRange()}
              readOnly
              className="w-full px-4 py-2 pr-10 bg-white border border-gray-300 rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-gazprom-blue"
              onClick={() => {
                // Здесь можно добавить date picker
                console.log('Open date picker');
              }}
            />
            <Calendar className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          </div>
        </div>

        {/* Тональность */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Тональность
          </label>
          <Dropdown
            isOpen={isTonalityDropdownOpen}
            onToggle={() => setIsTonalityDropdownOpen(!isTonalityDropdownOpen)}
            trigger={<span>{selectedTonalityName}</span>}
          >
            {tonalityOptions.map((option) => (
              <button
                key={option.value || 'all'}
                onClick={() => {
                  onTonalityChange?.(option.value);
                  setIsTonalityDropdownOpen(false);
                }}
                className="w-full px-4 py-2 text-left hover:bg-gray-100 focus:outline-none focus:bg-gray-100"
              >
                {option.label}
              </button>
            ))}
          </Dropdown>
        </div>

        {/* Продукт */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Продукт
          </label>
          <Dropdown
            isOpen={isProductDropdownOpen}
            onToggle={() => setIsProductDropdownOpen(!isProductDropdownOpen)}
            trigger={<span className="truncate">{selectedProductName}</span>}
          >
            <button
              onClick={() => {
                onProductChange?.(undefined);
                setIsProductDropdownOpen(false);
              }}
              className="w-full px-4 py-2 text-left hover:bg-gray-100 focus:outline-none focus:bg-gray-100"
            >
              Все
            </button>
            {products
              .filter(p => p.total_reviews > 0)
              .sort((a, b) => b.total_reviews - a.total_reviews)
              .map((product) => (
                <button
                  key={product.id}
                  onClick={() => {
                    onProductChange?.(product.id);
                    setIsProductDropdownOpen(false);
                  }}
                  className="w-full px-4 py-2 text-left hover:bg-gray-100 focus:outline-none focus:bg-gray-100 truncate"
                  title={product.name}
                >
                  {product.name}
                </button>
              ))}
          </Dropdown>
        </div>

        {/* Интервал (для графика динамики) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Интервал
          </label>
          <select
            value={interval}
            onChange={(e) => onIntervalChange?.(e.target.value as IntervalType)}
            className="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gazprom-blue"
          >
            {intervalOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Возможность выбрать все */}
        <div className="flex items-end">
          <div className="bg-white rounded-lg border border-gray-300 p-2 text-center min-w-[120px]">
            <div className="text-xs text-gray-600 mb-1">Все категории.</div>
            <div className="text-xs text-gray-600 mb-1">Видим кол-во</div>
            <div className="text-xs text-gray-600 mb-1">отзывов и</div>
            <div className="text-xs text-gray-600">соотношение</div>
            <div className="text-xs text-gray-600">тональностей</div>
          </div>
        </div>
      </div>

      {/* Кнопки действий */}
      <div className="flex justify-between items-center mt-4">
        <button
          onClick={() => {
            onProductChange?.(undefined);
            onTonalityChange?.(undefined);
            onDateRangeChange?.(undefined, undefined);
            onIntervalChange?.('month');
          }}
          className="text-sm text-gray-600 hover:text-gray-900"
        >
          Сбросить фильтры
        </button>

        <div className="text-sm text-gray-600">
          Возможность выбрать всё
        </div>
      </div>
    </div>
  );
}
