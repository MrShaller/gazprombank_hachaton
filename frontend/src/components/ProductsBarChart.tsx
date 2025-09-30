/**
 * Столбчатая диаграмма по продуктам/услугам
 */
'use client';

import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ChevronDown } from 'lucide-react';
import { formatNumber, truncateText } from '@/lib/utils';
import type { ProductStats } from '@/types/api';

interface ProductsBarChartProps {
  products: ProductStats[];
  className?: string;
}

export default function ProductsBarChart({
  products,
  className = '',
}: ProductsBarChartProps) {
  const [selectedTonality, setSelectedTonality] = useState<string>('all');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Маппинг сокращенных названий продуктов для лучшего отображения в диаграмме
  const getShortProductName = (fullName: string): string => {
    const shortNames: { [key: string]: string } = {
      'Дебетовые карты': 'Д. карты',
      'Кредитные карты': 'Кр. карты', 
      'Дистанционное обслуживание': 'Дист. обсл.',
      'Вклады': 'Вклады',
      'Другое': 'Другое',
      'Переводы': 'Переводы',
      'Мобильное приложение': 'Прилож.',
      'Кредиты': 'Кредиты',
      'Ипотека': 'Ипотека',
      'Автокредиты': 'Автокр.',
      'Рефинансирование': 'Рефин.',
    };
    
    return shortNames[fullName] || truncateText(fullName, 10);
  };

  // Опции тональности
  const tonalityOptions = [
    { value: 'all', label: 'Все', color: '#1e3a8a' },
    { value: 'positive', label: 'Положительная', color: '#22c55e' },
    { value: 'neutral', label: 'Нейтральная', color: '#6b7280' },
    { value: 'negative', label: 'Отрицательная', color: '#f97316' },
  ];

  const currentTonalityOption = tonalityOptions.find(opt => opt.value === selectedTonality) || tonalityOptions[0];

  // Функция для получения значения по выбранной тональности
  const getTonalityValue = (product: ProductStats, tonality: string) => {
    switch (tonality) {
      case 'positive': return product.positive_reviews;
      case 'negative': return product.negative_reviews;
      case 'neutral': return product.neutral_reviews;
      default: return product.total_reviews;
    }
  };

  // Функция для получения процента по выбранной тональности
  const getTonalityPercentage = (product: ProductStats, tonality: string) => {
    if (product.total_reviews === 0) return 0;
    const value = getTonalityValue(product, tonality);
    return tonality === 'all' ? 100 : (value / product.total_reviews) * 100;
  };

  // Подготовка данных для диаграммы - показываем все продукты
  const chartData = products
    .filter(product => product.total_reviews > 0)
    .sort((a, b) => getTonalityValue(b, selectedTonality) - getTonalityValue(a, selectedTonality))
    .map(product => ({
      name: getShortProductName(product.name),
      fullName: product.name,
      value: selectedTonality === 'all' ? getTonalityValue(product, selectedTonality) : getTonalityPercentage(product, selectedTonality),
      absoluteValue: getTonalityValue(product, selectedTonality),
      total: product.total_reviews,
      positive: product.positive_reviews,
      negative: product.negative_reviews,
      neutral: product.neutral_reviews,
      avgRating: product.avg_rating,
      percentage: getTonalityPercentage(product, selectedTonality),
    }));

  // Кастомный tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900 mb-2">{data.fullName}</p>
          
          <div className="space-y-1">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">
                {selectedTonality === 'all' ? 'Всего отзывов:' : `${currentTonalityOption.label}:`}
              </span>
              <span className="text-sm font-medium">
                {selectedTonality === 'all' 
                  ? formatNumber(data.absoluteValue)
                  : `${data.percentage.toFixed(1)}% (${formatNumber(data.absoluteValue)})`
                }
              </span>
            </div>
            
            {selectedTonality !== 'all' && (
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Всего отзывов:</span>
                <span className="text-sm font-medium">{formatNumber(data.total)}</span>
              </div>
            )}
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Положительные:</span>
              <span className="text-sm font-medium text-green-600">{formatNumber(data.positive)}</span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Нейтральные:</span>
              <span className="text-sm font-medium text-gray-600">{formatNumber(data.neutral)}</span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Отрицательные:</span>
              <span className="text-sm font-medium text-orange-600">{formatNumber(data.negative)}</span>
            </div>
            
            {data.avgRating && (
              <div className="flex justify-between items-center border-t pt-1 mt-2">
                <span className="text-sm text-gray-600">Средний рейтинг:</span>
                <span className="text-sm font-medium">★ {data.avgRating.toFixed(1)}</span>
              </div>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  // Кастомная метка на оси X
  const CustomXAxisTick = ({ x, y, payload }: any) => {
    return (
      <g transform={`translate(${x},${y})`}>
        <text 
          x={0} 
          y={0} 
          dy={20} 
          textAnchor="middle" 
          fill="#6b7280" 
          fontSize="12"
          transform="rotate(-45)"
        >
          {payload.value}
        </text>
      </g>
    );
  };

  return (
    <div className={`bg-white rounded-lg p-6 ${className}`}>
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Все продукты/услуги
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Количество отзывов по каждому продукту
            </p>
          </div>
          
          <div className="text-right">
            <div className="text-2xl font-bold text-gazprom-blue">
              {selectedTonality === 'all' 
                ? chartData.reduce((sum, p) => sum + p.absoluteValue, 0).toLocaleString('ru-RU')
                : `${(chartData.reduce((sum, p) => sum + p.percentage, 0) / chartData.length).toFixed(1)}%`
              }
            </div>
            <div className="text-sm text-gray-600">
              {selectedTonality === 'all' ? 'Всего отзывов' : `Средний % ${currentTonalityOption.label.toLowerCase()}`}
            </div>
          </div>
        </div>

        {/* Фильтр тональности */}
        <div className="flex items-center space-x-4">
          <label className="block text-sm font-medium text-gray-700">
            Тональность:
          </label>
          <div className="relative">
            <button
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="flex items-center justify-between w-48 px-3 py-2 text-left bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gazprom-blue"
            >
              <div className="flex items-center space-x-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: currentTonalityOption.color }}
                />
                <span>{currentTonalityOption.label}</span>
              </div>
              <ChevronDown className={`w-4 h-4 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
            </button>
            
            {isDropdownOpen && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-lg shadow-lg z-50">
                {tonalityOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => {
                      setSelectedTonality(option.value);
                      setIsDropdownOpen(false);
                    }}
                    className="w-full px-3 py-2 text-left hover:bg-gray-100 focus:outline-none focus:bg-gray-100 flex items-center space-x-2"
                  >
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: option.color }}
                    />
                    <span>{option.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* График */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="name"
              tick={<CustomXAxisTick />}
              interval={0}
              height={80}
            />
            <YAxis 
              tick={{ fontSize: 12 }}
              stroke="#6b7280"
              domain={selectedTonality === 'all' ? [0, 'dataMax'] : [0, 100]}
              tickFormatter={(value) => selectedTonality === 'all' ? formatNumber(value) : `${value}%`}
            />
            <Tooltip content={<CustomTooltip />} />
            
            <Bar 
              dataKey="value" 
              fill={currentTonalityOption.color}
              radius={[4, 4, 0, 0]}
              stroke={currentTonalityOption.color}
              strokeWidth={1}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Дополнительная информация */}
      {chartData.length === 0 && (
        <div className="text-center py-8">
          <div className="text-gray-500 text-sm">
            Нет данных для отображения
          </div>
        </div>
      )}


    </div>
  );
}
