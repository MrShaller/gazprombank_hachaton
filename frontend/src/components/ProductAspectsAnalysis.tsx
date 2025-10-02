/**
 * Компонент анализа аспектов продуктов (плюсы и минусы)
 */
'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { CheckCircle, XCircle, Star, ChevronUp, ChevronDown } from 'lucide-react';
import api from '@/lib/api';

interface ProductAspect {
  product_id: number;
  product_name: string;
  avg_rating: number | null;
  pros: string[];
  cons: string[];
  total_aspects: number;
}

interface ProductAspectsAnalysisProps {
  selectedProductIds?: number[];
  className?: string;
}

export default function ProductAspectsAnalysis({
  selectedProductIds = [],
  className = ''
}: ProductAspectsAnalysisProps) {
  const [aspects, setAspects] = useState<ProductAspect[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Состояние для сортировки
  const [sortField, setSortField] = useState<'name' | 'rating' | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  
  // Состояние для расширения списков аспектов
  const [expandedRows, setExpandedRows] = useState<{ [key: number]: { pros: boolean; cons: boolean } }>({});

  // Стабилизируем массив selectedProductIds для предотвращения бесконечных перерендеров
  const stableProductIds = useMemo(() => {
    return selectedProductIds?.length > 0 ? [...selectedProductIds].sort((a, b) => a - b) : [];
  }, [selectedProductIds]);

  useEffect(() => {
    let isCancelled = false;
    
    const fetchAspects = async () => {
      setLoading(true);
      setError(null);
      
      try {
        let response;
        
        // Используем API клиент вместо прямого fetch
        if (stableProductIds.length > 0) {
          response = await api.aspects.getMultipleProductsAspects({ 
            product_ids: stableProductIds 
          });
        } else {
          response = await api.aspects.getAllProductsAspects();
        }
        
        // Проверяем, не был ли запрос отменен
        if (!isCancelled) {
          setAspects(response.products || []);
        }
        
      } catch (err) {
        console.error('Ошибка загрузки анализа аспектов:', err);
        if (!isCancelled) {
          setError('Не удалось загрузить анализ аспектов');
        }
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    };

    fetchAspects();
    
    // Cleanup function для отмены запроса
    return () => {
      isCancelled = true;
    };
  }, [stableProductIds]);

  // Функция для получения цвета рейтинга
  const getRatingColor = useCallback((rating: number | null) => {
    if (!rating) return 'text-gray-400';
    if (rating >= 4) return 'text-green-500';
    if (rating >= 3) return 'text-yellow-500';
    return 'text-red-500';
  }, []);

  // Функция для форматирования рейтинга
  const formatRating = useCallback((rating: number | null) => {
    if (!rating) return 'Н/Д';
    return rating.toFixed(1);
  }, []);

  // Функция для сортировки
  const handleSort = useCallback((field: 'name' | 'rating') => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  }, [sortField, sortDirection]);

  // Функция для переключения расширения списка
  const toggleExpanded = useCallback((productId: number, type: 'pros' | 'cons') => {
    setExpandedRows(prev => ({
      ...prev,
      [productId]: {
        ...prev[productId],
        [type]: !prev[productId]?.[type]
      }
    }));
  }, []);

  // Сортированные аспекты
  const sortedAspects = useMemo(() => {
    if (!sortField) return aspects;

    return [...aspects].sort((a, b) => {
      let valueA: string | number = 0;
      let valueB: string | number = 0;

      if (sortField === 'name') {
        valueA = a.product_name?.toLowerCase?.() || "";
        valueB = b.product_name?.toLowerCase?.() || "";
      } else if (sortField === 'rating') {
        valueA = a.avg_rating ?? 0;
        valueB = b.avg_rating ?? 0;
      }

      if (valueA < valueB) return sortDirection === 'asc' ? -1 : 1;
      if (valueA > valueB) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [aspects, sortField, sortDirection]);

  // Условный рендеринг состояний
  if (loading) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-8 ${className}`}>
        <div className="flex items-center justify-center">
          <div className="loading-spinner" />
          <span className="ml-2 text-gray-600">Загрузка анализа аспектов...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-8 ${className}`}>
        <div className="text-center text-red-600">
          <XCircle className="w-12 h-12 mx-auto mb-4" />
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (aspects.length === 0) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-8 ${className}`}>
        <div className="text-center text-gray-500">
          <div className="text-lg font-medium mb-2">Анализ аспектов</div>
          <p>Нет данных для отображения</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      {/* Заголовок */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 rounded-t-lg">
        <div className="text-center space-y-2">
          <h3 className="text-lg font-semibold text-gray-900">
            Анализ аспектов | Оценка сильных сторон и зон роста
          </h3>
          <div className="flex flex-col sm:flex-row items-center justify-center space-y-1 sm:space-y-0 sm:space-x-4 text-xs text-gray-600">
            <div className="flex items-center space-x-1">
              <span>💡</span>
              <span>Кликните на "Продукт" или "Средняя оценка" для сортировки</span>
            </div>
            <div className="flex items-center space-x-1">
              <span>🤖</span>
              <span>Данные получены с помощью языкового моделирования</span>
            </div>
          </div>
        </div>
      </div>

      {/* Таблица */}
      <div className="overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gazprom-blue text-white">
            <tr>
              <th 
                className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors group"
                onClick={() => handleSort('name')}
                title="Кликните для сортировки по названию продукта"
              >
                <div className="flex items-center justify-center space-x-1">
                  <span>Продукт</span>
                  {sortField === 'name' ? (
                    sortDirection === 'asc' ? 
                      <ChevronUp className="w-4 h-4" /> : 
                      <ChevronDown className="w-4 h-4" />
                  ) : (
                    <div className="w-4 h-4 opacity-0 group-hover:opacity-50 transition-opacity">
                      <ChevronUp className="w-4 h-4" />
                    </div>
                  )}
                </div>
              </th>
              <th 
                className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors group"
                onClick={() => handleSort('rating')}
                title="Кликните для сортировки по средней оценке"
              >
                <div className="flex items-center justify-center space-x-1">
                  <span>Средняя оценка</span>
                  {sortField === 'rating' ? (
                    sortDirection === 'asc' ? 
                      <ChevronUp className="w-4 h-4" /> : 
                      <ChevronDown className="w-4 h-4" />
                  ) : (
                    <div className="w-4 h-4 opacity-0 group-hover:opacity-50 transition-opacity">
                      <ChevronUp className="w-4 h-4" />
                    </div>
                  )}
                </div>
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider">
                Преимущества
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider">
                Недостатки
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedAspects.map((product, index) => {
              const isExpandedPros = expandedRows[product.product_id]?.pros || false;
              const isExpandedCons = expandedRows[product.product_id]?.cons || false;
              
              return (
              <tr key={product.product_id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                {/* Продукт */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    {product.product_name}
                  </div>
                </td>

                {/* Средняя оценка */}
                <td className="px-6 py-4 whitespace-nowrap">
                  {product.avg_rating ? (
                    <div className="flex items-center">
                      <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                        product.avg_rating >= 4 
                          ? 'bg-green-100 text-green-800' 
                          : product.avg_rating >= 3 
                          ? 'bg-yellow-100 text-yellow-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {formatRating(product.avg_rating)} из 5
                      </div>
                    </div>
                  ) : (
                    <div className="text-sm text-gray-400">Н/Д</div>
                  )}
                </td>

                {/* Преимущества */}
                <td className="px-6 py-4">
                  <div className="space-y-1">
                    {(isExpandedPros ? product.pros : product.pros.slice(0, 3)).map((pro, idx) => (
                      <div key={idx} className="flex items-start">
                        <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 mr-2 flex-shrink-0" />
                        <span className="text-sm text-gray-700">{pro}</span>
                      </div>
                    ))}
                    {product.pros.length > 3 && !isExpandedPros && (
                      <button
                        onClick={() => toggleExpanded(product.product_id, 'pros')}
                        className="text-xs text-gazprom-blue hover:text-blue-700 ml-6 cursor-pointer underline"
                      >
                        +{product.pros.length - 3} ещё
                      </button>
                    )}
                    {product.pros.length > 3 && isExpandedPros && (
                      <button
                        onClick={() => toggleExpanded(product.product_id, 'pros')}
                        className="text-xs text-gazprom-blue hover:text-blue-700 ml-6 cursor-pointer underline"
                      >
                        Скрыть
                      </button>
                    )}
                    {product.pros.length === 0 && (
                      <div className="text-sm text-gray-400 italic">Нет данных</div>
                    )}
                  </div>
                </td>

                {/* Недостатки */}
                <td className="px-6 py-4">
                  <div className="space-y-1">
                    {(isExpandedCons ? product.cons : product.cons.slice(0, 3)).map((con, idx) => (
                      <div key={idx} className="flex items-start">
                        <XCircle className="w-4 h-4 text-red-500 mt-0.5 mr-2 flex-shrink-0" />
                        <span className="text-sm text-gray-700">{con}</span>
                      </div>
                    ))}
                    {product.cons.length > 3 && !isExpandedCons && (
                      <button
                        onClick={() => toggleExpanded(product.product_id, 'cons')}
                        className="text-xs text-gazprom-blue hover:text-blue-700 ml-6 cursor-pointer underline"
                      >
                        +{product.cons.length - 3} ещё
                      </button>
                    )}
                    {product.cons.length > 3 && isExpandedCons && (
                      <button
                        onClick={() => toggleExpanded(product.product_id, 'cons')}
                        className="text-xs text-gazprom-blue hover:text-blue-700 ml-6 cursor-pointer underline"
                      >
                        Скрыть
                      </button>
                    )}
                    {product.cons.length === 0 && (
                      <div className="text-sm text-gray-400 italic">Нет данных</div>
                    )}
                  </div>
                </td>
              </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
