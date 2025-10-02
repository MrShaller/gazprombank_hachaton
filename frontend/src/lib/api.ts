/**
 * API клиент для взаимодействия с backend
 */
import axios from 'axios';
import type {
  Product,
  Review,
  ProductsStatsResponse,
  TonalityDistributionResponse,
  TonalityDynamicsResponse,
  RatingDistribution,
  SummaryStats,
  AnalyticsFilters,
  IntervalType,
  ProductAspect,
  ProductAspectsResponse,
} from '@/types/api';

// Всегда используем относительный путь
const API_BASE_URL = '/api/v1';

console.log('API_BASE_URL:', API_BASE_URL);

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 0,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Интерцепторы для обработки ошибок
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

/**
 * API методы для продуктов
 */
export const productsApi = {
  /**
   * Получить все продукты
   */
  getAll: async (skip = 0, limit = 100): Promise<Product[]> => {
    const response = await apiClient.get<Product[]>('/products', {
      params: { skip, limit },
    });
    return response.data;
  },

  /**
   * Получить продукты с статистикой
   */
  getStats: async (): Promise<ProductsStatsResponse> => {
    const response = await apiClient.get<ProductsStatsResponse>('/products/stats');
    return response.data;
  },

  /**
   * Получить продукт по ID
   */
  getById: async (id: number): Promise<Product> => {
    const response = await apiClient.get<Product>(`/products/${id}`);
    return response.data;
  },
};

/**
 * API методы для отзывов
 */
export const reviewsApi = {
  /**
   * Получить отзывы с фильтрацией
   */
  getAll: async (params: {
    skip?: number;
    limit?: number;
    product_id?: number;
    tonality?: string;
    start_date?: string;
    end_date?: string;
  } = {}): Promise<Review[]> => {
    const response = await apiClient.get<Review[]>('/reviews', { params });
    return response.data;
  },

  /**
   * Получить количество отзывов
   */
  getCount: async (params: {
    product_id?: number;
    tonality?: string;
    start_date?: string;
    end_date?: string;
  } = {}): Promise<{ count: number }> => {
    const response = await apiClient.get<{ count: number }>('/reviews/count', { params });
    return response.data;
  },

  /**
   * Получить отзыв по ID
   */
  getById: async (id: number): Promise<Review> => {
    const response = await apiClient.get<Review>(`/reviews/${id}`);
    return response.data;
  },
};

/**
 * API методы для аналитики
 */
export const analyticsApi = {
  /**
   * Получить общую сводную статистику
   */
  getSummary: async (): Promise<SummaryStats> => {
    const response = await apiClient.get<SummaryStats>('/analytics/summary');
    return response.data;
  },

  /**
   * Получить распределение по тональностям
   */
  getTonalityDistribution: async (params: {
    product_id?: number;
    product_ids?: number[];
    start_date?: string;
    end_date?: string;
  } = {}): Promise<TonalityDistributionResponse> => {
    // Преобразуем product_ids в строку для API
    const apiParams: any = { ...params };
    if (params.product_ids && params.product_ids.length > 0) {
      apiParams.product_ids = params.product_ids.join(',');
      delete apiParams.product_id; // Удаляем устаревший параметр
    }
    
    const response = await apiClient.get<TonalityDistributionResponse>('/analytics/tonality', { params: apiParams });
    return response.data;
  },

  /**
   * Получить динамику тональностей
   */
  getTonalityDynamics: async (params: {
    product_id?: number;
    product_ids?: number[];
    start_date?: string;
    end_date?: string;
    interval?: IntervalType;
  } = {}): Promise<TonalityDynamicsResponse> => {
    // Преобразуем product_ids в строку для API
    const apiParams: any = { ...params };
    if (params.product_ids && params.product_ids.length > 0) {
      apiParams.product_ids = params.product_ids.join(',');
      delete apiParams.product_id; // Удаляем устаревший параметр
    }
    
    const response = await apiClient.get<TonalityDynamicsResponse>('/analytics/dynamics', { params: apiParams });
    return response.data;
  },

  /**
   * Получить распределение по рейтингам
   */
  getRatingDistribution: async (params: {
    product_id?: number;
    start_date?: string;
    end_date?: string;
  } = {}): Promise<{
    distribution: RatingDistribution[];
    total_reviews: number;
    average_rating: number;
  }> => {
    const response = await apiClient.get('/analytics/ratings', { params });
    return response.data;
  },

  /**
   * Получить топ отзывы
   */
  getTopReviews: async (params: {
    product_id?: number;
    tonality?: string;
    limit?: number;
  } = {}): Promise<{
    reviews: Review[];
    count: number;
  }> => {
    const response = await apiClient.get('/analytics/top-reviews', { params });
    return response.data;
  },
};

/**
 * Утилитарные функции для работы с API
 */
export const apiUtils = {
  /**
   * Проверка доступности API
   */
  healthCheck: async (): Promise<boolean> => {
    try {
      const response = await apiClient.get('/health');
      return response.status === 200;
    } catch {
      return false;
    }
  },

  /**
   * Получение информации об API
   */
  getInfo: async (): Promise<any> => {
    const response = await apiClient.get('/info');
    return response.data;
  },

  /**
   * Форматирование даты для API
   */
  formatDate: (date: Date): string => {
    return date.toISOString().split('T')[0];
  },

  /**
   * Парсинг даты из API
   */
  parseDate: (dateString: string): Date => {
    return new Date(dateString);
  },
};

/**
 * API для работы с анализом аспектов продуктов
 */
export const aspectsApi = {
  /**
   * Получить анализ аспектов для конкретного продукта
   */
  getProductAspects: async (productId: number): Promise<ProductAspect> => {
    const response = await apiClient.get<ProductAspect>(`/aspects/product/${productId}`);
    return response.data;
  },

  /**
   * Получить анализ аспектов для нескольких продуктов
   */
  getMultipleProductsAspects: async (params: {
    product_ids?: number[];
  } = {}): Promise<ProductAspectsResponse> => {
    let url = '/aspects/products';
    
    if (params.product_ids && params.product_ids.length > 0) {
      url += `?product_ids=${params.product_ids.join(',')}`;
    }
    
    const response = await apiClient.get<ProductAspectsResponse>(url);
    return response.data;
  },

  /**
   * Получить анализ аспектов для всех продуктов
   */
  getAllProductsAspects: async (): Promise<ProductAspectsResponse> => {
    const response = await apiClient.get<ProductAspectsResponse>('/aspects/all');
    return response.data;
  },
};

// Экспорт по умолчанию
const api = {
  products: productsApi,
  reviews: reviewsApi,
  analytics: analyticsApi,
  aspects: aspectsApi,
  utils: apiUtils,
};

export default api;
