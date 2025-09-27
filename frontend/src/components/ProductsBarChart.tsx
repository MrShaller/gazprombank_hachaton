/**
 * Столбчатая диаграмма по продуктам/услугам
 */
'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { formatNumber, truncateText } from '@/lib/utils';
import type { ProductStats } from '@/types/api';

interface ProductsBarChartProps {
  products: ProductStats[];
  className?: string;
  maxProducts?: number;
}

export default function ProductsBarChart({
  products,
  className = '',
  maxProducts = 10,
}: ProductsBarChartProps) {
  // Подготовка данных для диаграммы
  const chartData = products
    .filter(product => product.total_reviews > 0)
    .sort((a, b) => b.total_reviews - a.total_reviews)
    .slice(0, maxProducts)
    .map(product => ({
      name: truncateText(product.name, 15),
      fullName: product.name,
      value: product.total_reviews,
      positive: product.positive_reviews,
      negative: product.negative_reviews,
      neutral: product.neutral_reviews,
      avgRating: product.avg_rating,
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
              <span className="text-sm text-gray-600">Всего отзывов:</span>
              <span className="text-sm font-medium">{formatNumber(data.value)}</span>
            </div>
            
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
          dy={16} 
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
        <div className="flex items-center justify-between">
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
              {products.reduce((sum, p) => sum + p.total_reviews, 0).toLocaleString('ru-RU')}
            </div>
            <div className="text-sm text-gray-600">Всего отзывов</div>
          </div>
        </div>
      </div>

      {/* График */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="name"
              tick={<CustomXAxisTick />}
              interval={0}
              height={60}
            />
            <YAxis 
              tick={{ fontSize: 12 }}
              stroke="#6b7280"
              tickFormatter={(value) => formatNumber(value)}
            />
            <Tooltip content={<CustomTooltip />} />
            
            <Bar 
              dataKey="value" 
              fill="#1e3a8a"
              radius={[4, 4, 0, 0]}
              stroke="#1e2a5a"
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

      {/* Информация о количестве продуктов */}
      {products.length > maxProducts && (
        <div className="mt-4 text-center">
          <p className="text-xs text-gray-500">
            Показано топ-{maxProducts} продуктов из {products.length}
          </p>
        </div>
      )}

      {/* Легенда */}
      <div className="mt-4 flex justify-center">
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <div className="w-3 h-3 bg-gazprom-blue rounded"></div>
          <span>Общее количество отзывов</span>
        </div>
      </div>
    </div>
  );
}
