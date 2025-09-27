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
  selectedProductId?: number;
  selectedTonality?: string;
  startDate?: Date | null;
  endDate?: Date | null;
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
  const [isDatePickerOpen, setIsDatePickerOpen] = useState(false);
  
  // Локальное состояние для отслеживания выбора дат
  const [tempStartDate, setTempStartDate] = useState<Date | null>(startDate || null);
  const [tempEndDate, setTempEndDate] = useState<Date | null>(endDate || null);

  // Быстрые диапазоны дат (на основе реальных данных в БД)
  const quickDateRanges = [
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
              maxDate={new Date()}
              monthsShown={1}
              showYearDropdown
              showMonthDropdown
              dropdownMode="select"
              todayButton="Сегодня"
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
                console.log('🗑️ Reset dates button clicked');
                setTempStartDate(null);
                setTempEndDate(null);
                onDateRangeChange?.(undefined, undefined);
              }}
              className="px-2 py-1 text-xs text-gray-600 hover:text-gray-900 focus:outline-none"
            >
              Сбросить
            </button>
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
