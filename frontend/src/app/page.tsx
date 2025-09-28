/**
 * Главная страница дашборда
 */
'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import { AlertCircle, RefreshCw } from 'lucide-react';

// Компоненты
import FilterPanel from '@/components/FilterPanel';
import TonalityPieChart from '@/components/TonalityPieChart';
import ProductsList from '@/components/ProductsList';
import TonalityDynamicsChart from '@/components/TonalityDynamicsChart';
import ProductsBarChart from '@/components/ProductsBarChart';

// Хуки и утилиты
import { 
  useProductsStats, 
  useTonalityDistribution, 
  useTonalityDynamics,
  useSummaryStats,
  useApiHealth,
  useFilters 
} from '@/hooks/useApi';
import { getDefaultDateRange, dateToApiString } from '@/lib/utils';
import type { IntervalType } from '@/types/api';

export default function Dashboard() {
  // Состояние фильтров
  const { filters, updateFilter, resetFilters } = useFilters();
  
  // Состояние дат
  const [dateRange, setDateRange] = useState<{ start: Date | null; end: Date | null }>(() => {
    return { start: null, end: null };
  });

  // API данные
  const { data: productsStats, loading: productsLoading, error: productsError, refetch: refetchProducts } = useProductsStats();
  const { data: summaryStats, loading: summaryLoading, refetch: refetchSummary } = useSummaryStats();
  
  const { data: tonalityDistribution, loading: tonalityLoading, refetch: refetchTonality } = useTonalityDistribution({
    product_id: filters.product_id,
    product_ids: filters.product_ids && filters.product_ids.length > 0 ? filters.product_ids : undefined,
    start_date: dateRange.start ? dateToApiString(dateRange.start) : undefined,
    end_date: dateRange.end ? dateToApiString(dateRange.end) : undefined,
  });

  const { data: tonalityDynamics, loading: dynamicsLoading, refetch: refetchDynamics } = useTonalityDynamics({
    product_id: filters.product_id,
    product_ids: filters.product_ids && filters.product_ids.length > 0 ? filters.product_ids : undefined,
    start_date: dateRange.start ? dateToApiString(dateRange.start) : undefined,
    end_date: dateRange.end ? dateToApiString(dateRange.end) : undefined,
    interval: filters.interval,
  });

  const { isHealthy, checking: healthChecking } = useApiHealth();

  // Обработчики событий
  const handleProductChange = (productId?: number) => {
    updateFilter('product_id', productId);
  };

  const handleProductsChange = (productIds: number[]) => {
    updateFilter('product_ids', productIds);
    // Также обновляем старое поле для обратной совместимости
    updateFilter('product_id', productIds.length === 1 ? productIds[0] : undefined);
  };

  const handleTonalityChange = (tonality?: string) => {
    updateFilter('tonality', tonality);
  };

  const handleDateRangeChange = (startDate?: Date, endDate?: Date) => {
    console.log('handleDateRangeChange called with:', { startDate, endDate });
    
    if (startDate && endDate) {
      // Обе даты выбраны - устанавливаем диапазон
      console.log('Setting date range:', { start: startDate, end: endDate });
      setDateRange({ start: startDate, end: endDate });
    } else if (!startDate && !endDate) {
      // Обе даты сброшены - очищаем диапазон
      console.log('Clearing date range');
      setDateRange({ start: null, end: null });
    } else {
      console.log('Partial date selection, waiting for second date');
    }
    // Если выбрана только одна дата, ничего не делаем - ждем вторую
  };

  const handleIntervalChange = (interval: IntervalType) => {
    updateFilter('interval', interval);
  };

  const handleRefreshData = () => {
    refetchProducts();
    refetchSummary();
    refetchTonality();
    refetchDynamics();
  };

  // Проверка загрузки
  const isLoading = productsLoading || summaryLoading || tonalityLoading || dynamicsLoading;

  // Проверка ошибок
  const hasError = productsError || !isHealthy;

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Заголовок */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Image
                src="/logo-gazprombank.png"
                alt="Газпромбанк"
                width={40}
                height={40}
                className="h-10 w-auto"
              />
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  ГАЗПРОМБАНК
                </h1>
                <p className="text-sm text-gray-600">Контроль тональности</p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* Индикатор состояния API */}
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  isHealthy ? 'bg-green-500' : 'bg-red-500'
                }`} />
                <span className="text-sm text-gray-600">
                  {isHealthy ? 'Подключено' : 'Нет связи с API'}
                </span>
              </div>

              {/* Кнопка обновления */}
              <button
                onClick={handleRefreshData}
                disabled={isLoading}
                className="flex items-center space-x-2 px-3 py-2 text-sm bg-gazprom-blue text-white rounded-lg hover:bg-gazprom-blue-dark transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                <span>Обновить</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Основной контент */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Ошибка подключения */}
        {hasError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 text-red-600" />
              <div>
                <h3 className="text-sm font-medium text-red-800">
                  Проблема с подключением к API
                </h3>
                <p className="text-sm text-red-600 mt-1">
                  Убедитесь, что backend сервер запущен на http://localhost:8000
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Панель фильтров */}
        <FilterPanel
          products={productsStats?.products || []}
          selectedProductIds={filters.product_ids || []}
          startDate={dateRange.start}
          endDate={dateRange.end}
          onProductsChange={handleProductsChange}
          onDateRangeChange={handleDateRangeChange}
          className="mb-8"
        />

        {/* Основная сетка дашборда */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Круговая диаграмма тональностей */}
          <div className="lg:col-span-1">
            {tonalityDistribution && tonalityDistribution.distribution && tonalityDistribution.total_reviews !== undefined ? (
              <TonalityPieChart
                data={tonalityDistribution.distribution}
                totalReviews={tonalityDistribution.total_reviews}
                isFiltered={filters.product_id !== undefined || dateRange.start !== null || dateRange.end !== null}
                filterDescription={
                  filters.product_id 
                    ? `Данные для продукта: ${productsStats?.products.find(p => p.id === filters.product_id)?.name || 'Неизвестно'}`
                    : (dateRange.start || dateRange.end)
                      ? 'Данные за выбранный период'
                      : 'Общая диаграмма и данные без фильтров'
                }
              />
            ) : (
              <div className="bg-white rounded-lg p-6 h-96 flex items-center justify-center">
                <div className="loading-spinner" />
              </div>
            )}
          </div>

          {/* Список продуктов */}
          <div className="lg:col-span-1">
            {productsStats ? (
              <ProductsList
                products={productsStats.products}
                onProductSelect={handleProductChange}
                onProductsSelect={handleProductsChange}
                selectedProductId={filters.product_id}
                selectedProductIds={filters.product_ids}
                maxItems={8}
              />
            ) : (
              <div className="bg-white rounded-lg p-6 h-96 flex items-center justify-center">
                <div className="loading-spinner" />
              </div>
            )}
          </div>
        </div>

        {/* Нижняя секция с графиками */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* График динамики */}
          <div className="lg:col-span-1">
            {tonalityDynamics ? (
              <TonalityDynamicsChart
                data={tonalityDynamics.dynamics}
                interval={filters.interval}
                onIntervalChange={handleIntervalChange}
              />
            ) : (
              <div className="bg-white rounded-lg p-6 h-96 flex items-center justify-center">
                <div className="loading-spinner" />
              </div>
            )}
          </div>

          {/* Столбчатая диаграмма продуктов */}
          <div className="lg:col-span-1">
            {productsStats ? (
              <ProductsBarChart
                products={productsStats.products}
                maxProducts={10}
              />
            ) : (
              <div className="bg-white rounded-lg p-6 h-96 flex items-center justify-center">
                <div className="loading-spinner" />
              </div>
            )}
          </div>
        </div>

        {/* Кнопка "Продолжение страницы" */}
        <div className="mt-8 text-center">
          <button className="px-6 py-3 bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors">
            Продолжение страницы
          </button>
        </div>
      </main>

      {/* Футер */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-sm text-gray-600">
            © 2025 Газпромбанк. Дашборд анализа тональности отзывов клиентов.
          </div>
        </div>
      </footer>
    </div>
  );
}
