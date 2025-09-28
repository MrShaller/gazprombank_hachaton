/**
 * Панель фильтров для дашборда
 */
'use client';

import { useState } from 'react';
import { Calendar, ChevronDown } from 'lucide-react';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import type { ProductStats, IntervalType } from '@/types/api';

interface FilterPanelProps {
  products: ProductStats[];
  selectedProductIds?: number[];
  startDate?: Date | null;
  endDate?: Date | null;
  onProductsChange?: (productIds: number[]) => void;
  onDateRangeChange?: (startDate?: Date, endDate?: Date) => void;
  className?: string;
}

export default function FilterPanel({
  products,
  selectedProductIds = [],
  startDate,
  endDate,
  onProductsChange,
  onDateRangeChange,
  className = '',
}: FilterPanelProps) {
  const [isProductDropdownOpen, setIsProductDropdownOpen] = useState(false);
  
  // Локальное состояние для отслеживания выбора дат
  const [tempStartDate, setTempStartDate] = useState<Date | null>(startDate || null);
  const [tempEndDate, setTempEndDate] = useState<Date | null>(endDate || null);

  // Быстрые диапазоны дат (на основе реальных данных в БД)
  const quickDateRanges = [
    {
      label: 'Сегодня',
      getRange: () => ({
        start: new Date(2025, 4, 29), // 29 мая 2025 (последний день с данными)
        end: new Date(2025, 4, 29)    // 29 мая 2025
      })
    },
    {
      label: 'Май 2025',
      getRange: () => ({
        start: new Date(2025, 4, 1), // май (месяц 4 = май)
        end: new Date(2025, 4, 31)   // 31 мая
      })
    },
    {
      label: 'Последние 3 месяца',
      getRange: () => ({
        start: new Date(2025, 2, 1), // март (месяц 2 = март)
        end: new Date(2025, 4, 31)   // май (месяц 4 = май)
      })
    },
    {
      label: '2024 год',
      getRange: () => ({
        start: new Date(2024, 0, 1),  // 1 января
        end: new Date(2024, 11, 31)   // 31 декабря
      })
    },
    {
      label: '2025 год',
      getRange: () => ({
        start: new Date(2025, 0, 1),  // 1 января
        end: new Date(2025, 4, 31)    // 31 мая (до мая включительно)
      })
    }
  ];



  // Получаем названия выбранных продуктов
  const selectedProducts = products.filter(p => selectedProductIds.includes(p.id));
  const selectedProductsText = selectedProducts.length === 0 
    ? 'Все' 
    : selectedProducts.length === 1 
    ? selectedProducts[0].name
    : `Выбрано: ${selectedProducts.length}`;

  // Функция для переключения выбора продукта
  const toggleProduct = (productId: number) => {
    const newSelectedIds = selectedProductIds.includes(productId)
      ? selectedProductIds.filter(id => id !== productId) // Убираем если уже выбран
      : [...selectedProductIds, productId]; // Добавляем если не выбран
    
    onProductsChange?.(newSelectedIds);
  };

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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4">
        {/* Период */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Период
          </label>
          <div className="relative">
            <DatePicker
              selected={tempStartDate}
              onChange={(dates) => {
                console.log('🗓️ DatePicker onChange triggered!');
                console.log('  Raw dates:', dates);
                console.log('  Type:', typeof dates);
                console.log('  Is array:', Array.isArray(dates));
                
                if (Array.isArray(dates)) {
                  const [start, end] = dates as [Date | null, Date | null];
                  console.log('  📅 Array format detected:');
                  console.log('    Start date:', start ? start.toLocaleDateString('ru-RU') : 'null');
                  console.log('    End date:', end ? end.toLocaleDateString('ru-RU') : 'null');
                  
                  // Обновляем локальное состояние
                  setTempStartDate(start);
                  setTempEndDate(end);
                  
                  if (start && end) {
                    // Если выбраны обе даты, вызываем callback
                    console.log('  ✅ Both dates selected! Calling onDateRangeChange...');
                    onDateRangeChange?.(start, end);
                  } else if (!start && !end) {
                    // Если обе даты сброшены (через clear), сбрасываем фильтр
                    console.log('  🗑️ Clearing date range');
                    onDateRangeChange?.(undefined, undefined);
                  } else if (start && !end) {
                    // Выбрана только начальная дата - это нормально для диапазона
                    console.log('  ⏳ Start date selected, waiting for end date...');
                    // НЕ вызываем callback, просто ждем вторую дату
                  } else if (!start && end) {
                    console.log('  ⚠️ Only end date selected (unusual case)');
                  }
                } else {
                  // Если передана одна дата (не массив)
                  const singleDate = dates as Date | null;
                  console.log('  📅 Single date format:', singleDate ? singleDate.toLocaleDateString('ru-RU') : 'null');
                  if (!singleDate) {
                    console.log('  🗑️ Single date cleared');
                    onDateRangeChange?.(undefined, undefined);
                  }
                }
              }}
              startDate={tempStartDate}
              endDate={tempEndDate}
              selectsRange
              dateFormat="dd.MM.yyyy"
              placeholderText="XX.XX.XXXX — XX.XX.XXXX"
              locale={ru}
              className="w-full px-4 py-2 pr-8 bg-white border border-gray-300 rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-gazprom-blue"
              calendarClassName="border border-gray-300 rounded-lg shadow-lg"
              popperClassName="z-50"
              showPopperArrow={false}
              maxDate={new Date(2025, 4, 29)} // 29 мая 2025
              monthsShown={1}
              showYearDropdown
              showMonthDropdown
              dropdownMode="select"
              openToDate={new Date(2025, 4, 29)} // Открывается на мае 2025 (29 мая)
              shouldCloseOnSelect={false}
              disabledKeyboardNavigation={false}
              onSelect={(date: Date | null) => {
                console.log('🖱️ Date clicked/selected:', date ? date.toLocaleDateString('ru-RU') : 'null');
              }}
              onCalendarOpen={() => {
                console.log('📅 Calendar opened');
              }}
              onCalendarClose={() => {
                console.log('📅 Calendar closed');
              }}
            />
            <Calendar className="absolute right-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
          
          {/* Быстрые кнопки выбора периода */}
          <div className="flex flex-wrap gap-1 mt-2">
            {quickDateRanges.map((range, index) => (
              <button
                key={index}
                onClick={() => {
                  const { start, end } = range.getRange();
                  console.log('🚀 Quick button clicked:', range.label);
                  console.log('  Setting dates:', start.toLocaleDateString('ru-RU'), '-', end.toLocaleDateString('ru-RU'));
                  
                  // Обновляем локальное состояние
                  setTempStartDate(start);
                  setTempEndDate(end);
                  
                  // Вызываем callback
                  onDateRangeChange?.(start, end);
                }}
                className="px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50 focus:outline-none focus:ring-1 focus:ring-gazprom-blue"
              >
                {range.label}
              </button>
            ))}
            <button
              onClick={() => {
                console.log('📅 All time button clicked');
                setTempStartDate(null);
                setTempEndDate(null);
                onDateRangeChange?.(undefined, undefined);
              }}
              className="px-2 py-1 text-xs bg-gazprom-blue text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-1 focus:ring-gazprom-blue"
            >
              За всё время
            </button>
          </div>
        </div>


        {/* Продукт */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Продукт
          </label>
          <Dropdown
            isOpen={isProductDropdownOpen}
            onToggle={() => setIsProductDropdownOpen(!isProductDropdownOpen)}
            trigger={<span className="truncate">{selectedProductsText}</span>}
          >
            <button
              onClick={() => {
                onProductsChange?.([]);
                setIsProductDropdownOpen(false);
              }}
              className="w-full px-4 py-2 text-left hover:bg-gray-100 focus:outline-none focus:bg-gray-100 border-b border-gray-200"
            >
              <div className="flex items-center justify-between">
                <span>Все продукты</span>
                {selectedProductIds.length === 0 && (
                  <span className="text-gazprom-blue">✓</span>
                )}
              </div>
            </button>
            {products
              .filter(p => p.total_reviews > 0)
              .sort((a, b) => b.total_reviews - a.total_reviews)
              .map((product) => (
                <button
                  key={product.id}
                  onClick={() => {
                    toggleProduct(product.id);
                    // НЕ закрываем dropdown для множественного выбора
                  }}
                  className="w-full px-4 py-2 text-left hover:bg-gray-100 focus:outline-none focus:bg-gray-100 truncate"
                  title={product.name}
                >
                  <div className="flex items-center justify-between">
                    <span className={selectedProductIds.includes(product.id) ? 'font-medium text-gazprom-blue' : ''}>
                      {product.name}
                    </span>
                    {selectedProductIds.includes(product.id) && (
                      <span className="text-gazprom-blue">✓</span>
                    )}
                  </div>
                </button>
              ))}
          </Dropdown>
        </div>


      </div>

      {/* Кнопки действий */}
      <div className="flex justify-between items-center mt-4">
        <button
          onClick={() => {
            onProductsChange?.([]);
            onDateRangeChange?.(undefined, undefined);
          }}
          className="text-sm text-gray-600 hover:text-gray-900"
        >
          Сбросить фильтры
        </button>

      </div>
    </div>
  );
}
