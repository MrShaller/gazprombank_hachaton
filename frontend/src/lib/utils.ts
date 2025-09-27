/**
 * Утилитарные функции для фронтенда
 */
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, parseISO, startOfMonth, endOfMonth, subMonths } from 'date-fns';
import { ru } from 'date-fns/locale';

/**
 * Объединение CSS классов с поддержкой Tailwind
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Форматирование чисел
 */
export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('ru-RU').format(num);
};

/**
 * Форматирование процентов
 */
export const formatPercent = (num: number, decimals = 1): string => {
  return `${num.toFixed(decimals)}%`;
};

/**
 * Форматирование дат
 */
export const formatDate = (date: string | Date, formatStr = 'dd.MM.yyyy'): string => {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, formatStr, { locale: ru });
};

/**
 * Форматирование дат для отображения в графиках
 */
export const formatChartDate = (date: string, interval: 'day' | 'week' | 'month' = 'month'): string => {
  const dateObj = parseISO(date);
  
  switch (interval) {
    case 'day':
      return format(dateObj, 'dd.MM', { locale: ru });
    case 'week':
      return format(dateObj, 'dd.MM', { locale: ru });
    case 'month':
      return format(dateObj, 'MMM yyyy', { locale: ru });
    default:
      return format(dateObj, 'dd.MM.yyyy', { locale: ru });
  }
};

/**
 * Получение цвета для тональности
 */
export const getTonalityColor = (tonality: string): string => {
  switch (tonality) {
    case 'положительно':
      return '#22c55e'; // green-500
    case 'отрицательно':
      return '#f97316'; // orange-500
    case 'нейтрально':
      return '#6b7280'; // gray-500
    default:
      return '#6b7280';
  }
};

/**
 * Получение читаемого названия тональности
 */
export const getTonalityLabel = (tonality: string): string => {
  switch (tonality) {
    case 'положительно':
      return 'Положительная';
    case 'отрицательно':
      return 'Отрицательная';
    case 'нейтрально':
      return 'Нейтральная';
    default:
      return tonality;
  }
};

/**
 * Получение короткого названия тональности
 */
export const getTonalityShortLabel = (tonality: string): string => {
  switch (tonality) {
    case 'положительно':
      return 'Позитив.';
    case 'отрицательно':
      return 'Негатив.';
    case 'нейтрально':
      return 'Нейтр.';
    default:
      return tonality;
  }
};

/**
 * Генерация диапазона дат по умолчанию (последние 12 месяцев)
 */
export const getDefaultDateRange = (): { start: Date; end: Date } => {
  const end = endOfMonth(new Date());
  const start = startOfMonth(subMonths(end, 11));
  
  return { start, end };
};

/**
 * Преобразование даты в строку для API
 */
export const dateToApiString = (date: Date): string => {
  return date.toISOString().split('T')[0];
};

/**
 * Получение цвета для рейтинга
 */
export const getRatingColor = (rating: number): string => {
  if (rating >= 4) return '#22c55e'; // green-500
  if (rating >= 3) return '#eab308'; // yellow-500
  return '#ef4444'; // red-500
};

/**
 * Сортировка продуктов по количеству отзывов
 */
export const sortProductsByReviews = <T extends { total_reviews: number }>(products: T[]): T[] => {
  return [...products].sort((a, b) => b.total_reviews - a.total_reviews);
};

/**
 * Группировка данных по ключу
 */
export const groupBy = <T, K extends keyof any>(
  array: T[],
  getKey: (item: T) => K
): Record<K, T[]> => {
  return array.reduce((result, item) => {
    const key = getKey(item);
    (result[key] = result[key] || []).push(item);
    return result;
  }, {} as Record<K, T[]>);
};

/**
 * Дебаунс функция
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

/**
 * Проверка на мобильное устройство
 */
export const isMobile = (): boolean => {
  if (typeof window === 'undefined') return false;
  return window.innerWidth < 768;
};

/**
 * Получение контрастного цвета для фона
 */
export const getContrastColor = (backgroundColor: string): string => {
  // Простая проверка яркости цвета
  const hex = backgroundColor.replace('#', '');
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);
  
  const brightness = (r * 299 + g * 587 + b * 114) / 1000;
  return brightness > 128 ? '#000000' : '#ffffff';
};

/**
 * Сокращение длинного текста
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

/**
 * Валидация email
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Генерация уникального ID
 */
export const generateId = (): string => {
  return Math.random().toString(36).substr(2, 9);
};
