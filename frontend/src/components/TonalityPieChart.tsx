/**
 * Круговая диаграмма распределения тональностей
 */
'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { getTonalityColor, getTonalityLabel, formatPercent } from '@/lib/utils';
import type { TonalityDistribution } from '@/types/api';

interface TonalityPieChartProps {
  data: TonalityDistribution[];
  totalReviews: number;
  className?: string;
  isFiltered?: boolean;
  filterDescription?: string;
}

export default function TonalityPieChart({ 
  data, 
  totalReviews, 
  className = '',
  isFiltered = false,
  filterDescription = ''
}: TonalityPieChartProps) {
  // Подготовка данных для диаграммы
  const chartData = data.map(item => ({
    name: getTonalityLabel(item.tonality),
    value: item.count,
    percentage: item.percentage,
    color: getTonalityColor(item.tonality),
    tonality: item.tonality,
  }));

  // Кастомный компонент для отображения значений в tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">{data.name}</p>
          <p className="text-sm text-gray-600">
            Отзывов: <span className="font-medium">{data.value.toLocaleString('ru-RU')}</span>
          </p>
          <p className="text-sm text-gray-600">
            Доля: <span className="font-medium">{formatPercent(data.percentage)}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  // Кастомная легенда
  const CustomLegend = ({ payload }: any) => {
    return (
      <div className="flex flex-col space-y-2 mt-4">
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center space-x-2">
            <div 
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-sm text-gray-700">
              {entry.value}
            </span>
          </div>
        ))}
      </div>
    );
  };

  // Кастомные метки на диаграмме
  const renderLabel = ({ percentage }: { percentage: number }) => {
    if (percentage > 5) { // Показываем метки только для сегментов больше 5%
      return `${formatPercent(percentage)}`;
    }
    return '';
  };

  return (
    <div className={`bg-white rounded-lg p-6 ${className}`}>
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Распределение тональностей
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          {isFiltered ? filterDescription : 'Общая диаграмма и данные без фильтров'}
        </p>
      </div>

      <div className="flex flex-col lg:flex-row items-center">
        {/* Диаграмма */}
        <div className="w-full lg:w-2/3 h-80">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderLabel}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
                stroke="#fff"
                strokeWidth={2}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Статистика и легенда */}
        <div className="w-full lg:w-1/3 lg:pl-6">
          <div className="text-center lg:text-left mb-6">
            <div className="text-3xl font-bold text-gazprom-blue mb-1">
              {(totalReviews || 0).toLocaleString('ru-RU')}
            </div>
            <div className="text-sm text-gray-600">Всего отзывов</div>
          </div>

          {/* Детальная статистика */}
          <div className="space-y-3">
            {chartData.map((item, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div 
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-sm text-gray-700">{item.name}</span>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900">
                    {item.value.toLocaleString('ru-RU')}
                  </div>
                  <div className="text-xs text-gray-500">
                    {formatPercent(item.percentage)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Дополнительная информация */}
      {data.length === 0 && (
        <div className="text-center py-8">
          <div className="text-gray-500 text-sm">
            Нет данных для отображения
          </div>
        </div>
      )}
    </div>
  );
}
