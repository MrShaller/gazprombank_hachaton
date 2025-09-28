/**
 * График динамики изменения тональностей
 */
'use client';

import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ChevronDown, Maximize2 } from 'lucide-react';
import { formatChartDate, getTonalityColor, getTonalityLabel } from '@/lib/utils';
import type { DynamicsPoint, IntervalType } from '@/types/api';

interface TonalityDynamicsChartProps {
  data: DynamicsPoint[];
  interval?: IntervalType;
  onIntervalChange?: (interval: IntervalType) => void;
  className?: string;
}

export default function TonalityDynamicsChart({
  data,
  interval = 'month',
  onIntervalChange,
  className = '',
}: TonalityDynamicsChartProps) {
  const [showPercentage, setShowPercentage] = useState(true);
  const [isIntervalDropdownOpen, setIsIntervalDropdownOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  // Опции интервалов
  const intervalOptions = [
    { value: 'day' as IntervalType, label: 'День' },
    { value: 'week' as IntervalType, label: 'Неделя' },
    { value: 'month' as IntervalType, label: 'Месяц' },
  ];

  const currentIntervalOption = intervalOptions.find(opt => opt.value === interval) || intervalOptions[2];
  // Подготовка данных для графика
  const chartData = data.map(point => ({
    date: formatChartDate(point.date, interval),
    fullDate: point.date,
    positive: showPercentage ? point.positive_percentage : point.positive_count,
    negative: showPercentage ? point.negative_percentage : point.negative_count,
    neutral: showPercentage ? point.neutral_percentage : point.neutral_count,
    total: point.total_count,
    // Дополнительные данные для tooltip
    positive_count: point.positive_count,
    negative_count: point.negative_count,
    neutral_count: point.neutral_count,
    positive_percentage: point.positive_percentage,
    negative_percentage: point.negative_percentage,
    neutral_percentage: point.neutral_percentage,
  }));

  // Кастомный tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900 mb-2">{label}</p>
          <p className="text-xs text-gray-600 mb-2">
            Всего отзывов: {data.total.toLocaleString('ru-RU')}
          </p>
          
          <div className="space-y-1">
            {payload.map((entry: any, index: number) => {
              const tonality = entry.dataKey;
              let tonalityKey = '';
              let color = '';
              
              switch (tonality) {
                case 'positive':
                  tonalityKey = 'положительно';
                  color = getTonalityColor('положительно');
                  break;
                case 'negative':
                  tonalityKey = 'отрицательно';
                  color = getTonalityColor('отрицательно');
                  break;
                case 'neutral':
                  tonalityKey = 'нейтрально';
                  color = getTonalityColor('нейтрально');
                  break;
              }
              
              const count = data[`${tonality}_count`];
              const percentage = data[`${tonality}_percentage`];
              
              return (
                <div key={index} className="flex items-center justify-between space-x-4">
                  <div className="flex items-center space-x-2">
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: color }}
                    />
                    <span className="text-sm text-gray-700">
                      {getTonalityLabel(tonalityKey)}
                    </span>
                  </div>
                  <div className="text-sm font-medium">
                    {count.toLocaleString('ru-RU')} ({percentage.toFixed(1)}%)
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      );
    }
    return null;
  };

  // Кастомная легенда
  const CustomLegend = ({ payload }: any) => {
    return (
      <div className="flex justify-center space-x-6 mt-4">
        {payload.map((entry: any, index: number) => {
          let label = '';
          switch (entry.dataKey) {
            case 'positive':
              label = 'Положительная';
              break;
            case 'negative':
              label = 'Отрицательная';
              break;
            case 'neutral':
              label = 'Нейтральная';
              break;
          }
          
          return (
            <div key={index} className="flex items-center space-x-2">
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-sm text-gray-700">{label}</span>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className={`bg-white rounded-lg p-6 ${className}`}>
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Динамика изменения тональностей
            </h3>
          </div>
          
          <button 
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center space-x-2 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
          >
            <Maximize2 className="w-4 h-4" />
            <span>Развернуть диаграмму</span>
          </button>
        </div>

        {/* Панель управления */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* Интервал */}
            <div className="flex items-center space-x-2">
              <label className="block text-sm font-medium text-gray-700">
                Интервал:
              </label>
              <div className="relative">
                <button
                  onClick={() => setIsIntervalDropdownOpen(!isIntervalDropdownOpen)}
                  className="flex items-center justify-between w-24 px-3 py-2 text-left bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gazprom-blue"
                >
                  <span className="text-sm">{currentIntervalOption.label}</span>
                  <ChevronDown className={`w-4 h-4 transition-transform ${isIntervalDropdownOpen ? 'rotate-180' : ''}`} />
                </button>
                
                {isIntervalDropdownOpen && (
                  <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-lg shadow-lg z-50">
                    {intervalOptions.map((option) => (
                      <button
                        key={option.value}
                        onClick={() => {
                          onIntervalChange?.(option.value);
                          setIsIntervalDropdownOpen(false);
                        }}
                        className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 focus:outline-none focus:bg-gray-100"
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Переключатель режима отображения */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setShowPercentage(true)}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                showPercentage 
                  ? 'bg-white text-gray-900 shadow-sm' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Проценты
            </button>
            <button
              onClick={() => setShowPercentage(false)}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                !showPercentage 
                  ? 'bg-white text-gray-900 shadow-sm' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Количество
            </button>
          </div>
        </div>
      </div>

      {/* График */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 12 }}
              stroke="#6b7280"
            />
            <YAxis 
              tick={{ fontSize: 12 }}
              stroke="#6b7280"
              domain={showPercentage ? [0, 100] : undefined}
              tickFormatter={(value) => showPercentage ? `${value}%` : value.toString()}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend content={<CustomLegend />} />
            
            <Line
              type="monotone"
              dataKey="positive"
              stroke={getTonalityColor('положительно')}
              strokeWidth={3}
              dot={{ fill: getTonalityColor('положительно'), strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: getTonalityColor('положительно'), strokeWidth: 2 }}
            />
            <Line
              type="monotone"
              dataKey="neutral"
              stroke={getTonalityColor('нейтрально')}
              strokeWidth={3}
              dot={{ fill: getTonalityColor('нейтрально'), strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: getTonalityColor('нейтрально'), strokeWidth: 2 }}
            />
            <Line
              type="monotone"
              dataKey="negative"
              stroke={getTonalityColor('отрицательно')}
              strokeWidth={3}
              dot={{ fill: getTonalityColor('отрицательно'), strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: getTonalityColor('отрицательно'), strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Дополнительная информация */}
      {data.length === 0 && (
        <div className="text-center py-8">
          <div className="text-gray-500 text-sm">
            Нет данных для отображения динамики
          </div>
        </div>
      )}

    </div>
  );
}
