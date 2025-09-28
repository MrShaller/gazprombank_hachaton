/**
 * Хуки для работы с API
 */
import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import type {
  ProductsStatsResponse,
  TonalityDistributionResponse,
  TonalityDynamicsResponse,
  SummaryStats,
  IntervalType,
} from '@/types/api';

/**
 * Общий хук для API запросов с состоянием загрузки
 */
function useApiCall<T>(
  apiCall: () => Promise<T>,
  dependencies: any[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiCall();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Произошла ошибка');
      console.error('API Error:', err);
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

/**
 * Хук для получения статистики продуктов
 */
export function useProductsStats() {
  return useApiCall<ProductsStatsResponse>(() => api.products.getStats());
}

/**
 * Хук для получения общей сводной статистики (без фильтров)
 */
export function useSummaryStats() {
  return useApiCall<SummaryStats>(() => api.analytics.getSummary());
}

/**
 * Хук для получения распределения тональностей
 */
export function useTonalityDistribution(params: {
  product_id?: number;
  product_ids?: number[];
  start_date?: string;
  end_date?: string;
} = {}) {
  return useApiCall<TonalityDistributionResponse>(
    () => api.analytics.getTonalityDistribution(params),
    [params.product_id, JSON.stringify(params.product_ids), params.start_date, params.end_date]
  );
}

/**
 * Хук для получения динамики тональностей
 */
export function useTonalityDynamics(params: {
  product_id?: number;
  product_ids?: number[];
  start_date?: string;
  end_date?: string;
  interval?: IntervalType;
} = {}) {
  return useApiCall<TonalityDynamicsResponse>(
    () => api.analytics.getTonalityDynamics(params),
    [params.product_id, JSON.stringify(params.product_ids), params.start_date, params.end_date, params.interval]
  );
}

/**
 * Хук для получения распределения рейтингов
 */
export function useRatingDistribution(params: {
  product_id?: number;
  start_date?: string;
  end_date?: string;
} = {}) {
  return useApiCall(
    () => api.analytics.getRatingDistribution(params),
    [params.product_id, params.start_date, params.end_date]
  );
}

/**
 * Хук для проверки состояния API
 */
export function useApiHealth() {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [checking, setChecking] = useState(false);

  const checkHealth = useCallback(async () => {
    setChecking(true);
    try {
      const healthy = await api.utils.healthCheck();
      setIsHealthy(healthy);
    } catch {
      setIsHealthy(false);
    } finally {
      setChecking(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    
    // Проверяем состояние каждые 30 секунд
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  return { isHealthy, checking, checkHealth };
}

/**
 * Хук для фильтров с локальным состоянием
 */
export function useFilters() {
  const [filters, setFilters] = useState({
    product_id: undefined as number | undefined, // Оставляем для обратной совместимости
    product_ids: [] as number[], // Новое поле для множественного выбора
    start_date: undefined as string | undefined,
    end_date: undefined as string | undefined,
    tonality: undefined as string | undefined,
    interval: 'month' as IntervalType,
  });

  const updateFilter = useCallback((key: string, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters({
      product_id: undefined,
      product_ids: [],
      start_date: undefined,
      end_date: undefined,
      tonality: undefined,
      interval: 'month',
    });
  }, []);

  return { filters, updateFilter, resetFilters };
}

/**
 * Хук для управления состоянием загрузки множественных запросов
 */
export function useMultipleApiCalls() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeMultiple = useCallback(async <T>(
    calls: (() => Promise<T>)[]
  ): Promise<T[]> => {
    setLoading(true);
    setError(null);
    
    try {
      const results = await Promise.all(calls.map(call => call()));
      return results;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Произошла ошибка';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, error, executeMultiple };
}
