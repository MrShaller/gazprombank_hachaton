/**
 * Типы данных для API дашборда отзывов Газпромбанка
 */

export interface Product {
  id: number;
  name: string;
  created_at: string;
}

export interface Review {
  id: number;
  review_id: string;
  product_id: number;
  review_text: string;
  review_date: string;
  url?: string;
  parsed_at: string;
  bank_name: string;
  rating: number;
  tonality: 'положительно' | 'отрицательно' | 'нейтрально';
  validation?: string;
  is_valid: boolean;
  created_at: string;
  product: Product;
}

export interface ProductStats {
  id: number;
  name: string;
  total_reviews: number;
  positive_reviews: number;
  negative_reviews: number;
  neutral_reviews: number;
  positive_percentage: number;
  negative_percentage: number;
  neutral_percentage: number;
  avg_rating?: number;
  first_review?: string;
  last_review?: string;
}

export interface TonalityDistribution {
  tonality: string;
  count: number;
  percentage: number;
  avg_rating?: number;
}

export interface TonalityDistributionResponse {
  distribution: TonalityDistribution[];
  total_reviews: number;
  filters: {
    product_id?: number;
    start_date?: string;
    end_date?: string;
  };
}

export interface DynamicsPoint {
  date: string;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  total_count: number;
  positive_percentage: number;
  negative_percentage: number;
  neutral_percentage: number;
}

export interface TonalityDynamicsResponse {
  dynamics: DynamicsPoint[];
  total_periods: number;
  total_reviews: number;
  interval: 'day' | 'week' | 'month';
  filters: {
    product_id?: number;
    start_date?: string;
    end_date?: string;
  };
}

export interface RatingDistribution {
  rating: number;
  count: number;
  percentage: number;
}

export interface SummaryStats {
  total_reviews: number;
  total_products: number;
  avg_rating?: number;
  positive_reviews: number;
  negative_reviews: number;
  neutral_reviews: number;
  first_review_date?: string;
  last_review_date?: string;
  positive_percentage: number;
  negative_percentage: number;
  neutral_percentage: number;
}

export interface ProductsStatsResponse {
  products: ProductStats[];
  total_products: number;
  products_with_reviews: number;
}

// Типы для фильтров
export interface DateFilter {
  start_date?: string;
  end_date?: string;
}

export interface AnalyticsFilters {
  product_id?: number;
  tonality?: 'положительно' | 'отрицательно' | 'нейтрально';
  date_filter?: DateFilter;
}

// Утилитарные типы
export type TonalityType = 'положительно' | 'отрицательно' | 'нейтрально';
export type IntervalType = 'day' | 'week' | 'month';

// Константы для тональностей
export const TONALITY_LABELS = {
  'положительно': 'Положительная',
  'отрицательно': 'Отрицательная',
  'нейтрально': 'Нейтральная',
} as const;

export const TONALITY_COLORS = {
  'положительно': '#22c55e',
  'отрицательно': '#f97316', 
  'нейтрально': '#6b7280',
} as const;

// Типы для анализа аспектов продуктов
export interface ProductAspect {
  product_id: number;
  product_name: string;
  avg_rating: number | null;
  pros: string[];
  cons: string[];
  total_aspects: number;
}

export interface ProductAspectsResponse {
  products: ProductAspect[];
  total_products: number;
  filters: {
    product_ids?: number[];
  };
}
