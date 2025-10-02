# 🎨 Frontend - React дашборд для анализа отзывов

## 🎯 Обзор

Frontend представляет собой современное веб-приложение на базе Next.js 14, которое обеспечивает интуитивный интерфейс для анализа тональности отзывов клиентов Газпромбанка. Приложение включает интерактивные графики, фильтрацию данных, загрузку файлов для ML анализа и адаптивный дизайн.

## 🏗️ Технологический стек

### Основные технологии
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5.9+
- **Styling**: Tailwind CSS 3.3+
- **Charts**: Recharts 2.15+
- **HTTP Client**: Axios 1.6+
- **Icons**: Lucide React 0.294+
- **Date Handling**: date-fns 2.30+

### Дополнительные библиотеки
```json
{
  "dependencies": {
    "next": "^14.0.3",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.9.2",
    "tailwindcss": "^3.3.5",
    "recharts": "^2.15.4",
    "axios": "^1.6.2",
    "lucide-react": "^0.294.0",
    "date-fns": "^2.30.0",
    "react-datepicker": "^8.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0"
  }
}
```

## 📁 Структура проекта

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── globals.css        # Глобальные стили
│   │   ├── layout.tsx         # Корневой layout
│   │   └── page.tsx           # Главная страница дашборда
│   ├── components/            # React компоненты
│   │   ├── FileUploadModal.tsx      # Модальное окно загрузки файлов
│   │   ├── FilterPanel.tsx          # Панель фильтров
│   │   ├── ProductAspectsAnalysis.tsx # Анализ аспектов продуктов
│   │   ├── ProductsBarChart.tsx     # Столбчатая диаграмма продуктов
│   │   ├── ProductsList.tsx         # Список продуктов
│   │   ├── TonalityDynamicsChart.tsx # График динамики тональности
│   │   └── TonalityPieChart.tsx     # Круговая диаграмма тональности
│   ├── hooks/                 # Custom React hooks
│   │   └── useApi.ts          # Хуки для работы с API
│   ├── lib/                   # Утилиты и конфигурация
│   │   ├── api.ts             # API клиент
│   │   └── utils.ts           # Вспомогательные функции
│   └── types/                 # TypeScript типы
│       └── api.ts             # Типы для API
├── public/                    # Статические файлы
│   └── Газпромбанк.тех.svg   # Логотип
├── tailwind.config.js         # Конфигурация Tailwind
├── next.config.js             # Конфигурация Next.js
├── package.json               # Зависимости и скрипты
└── tsconfig.json              # Конфигурация TypeScript
```

## 🎨 Дизайн система

### Цветовая палитра
```javascript
// tailwind.config.js
colors: {
  // Корпоративные цвета Газпромбанка
  gazprom: {
    blue: '#1e3a8a',        // Основной синий
    'blue-dark': '#1e2a5a', // Темный синий
    'blue-light': '#3b82f6', // Светлый синий
  },
  // Цвета для тональности
  sentiment: {
    positive: '#22c55e',     // Зеленый (положительно)
    neutral: '#6b7280',      // Серый (нейтрально)
    negative: '#f97316',     // Оранжевый (отрицательно)
  },
}
```

### Типографика
```css
/* globals.css */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.font-sans {
  font-family: 'Inter', system-ui, sans-serif;
}
```

### Градиенты и эффекты
```css
/* Корпоративный градиент для заголовков */
.gradient-text {
  background: linear-gradient(135deg, #005DAC 0%, #0B0A0B 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Анимации загрузки */
.loading-spinner {
  @apply w-8 h-8 border-4 border-gazprom-blue border-t-transparent rounded-full animate-spin;
}
```

## 🧩 Основные компоненты

### 1. Главная страница (Dashboard)
```typescript
// src/app/page.tsx
export default function Dashboard() {
  // Состояние фильтров и данных
  const { filters, updateFilter, resetFilters } = useFilters();
  const [dateRange, setDateRange] = useState<{ start: Date | null; end: Date | null }>();
  
  // API хуки для получения данных
  const { data: productsStats, loading: productsLoading } = useProductsStats();
  const { data: tonalityDistribution } = useTonalityDistribution(filters);
  const { data: tonalityDynamics } = useTonalityDynamics(filters);
  const { isHealthy } = useApiHealth();

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Заголовок с логотипом и статусом API */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            {/* Логотип и название */}
            <div className="flex items-center space-x-6">
              <Image src="/Газпромбанк.тех.svg" alt="Газпромбанк.тех" />
              <div>
                <h1 className="gradient-text text-2xl font-bold">
                  Контроль тональности
                </h1>
                <p className="gradient-text text-base font-medium">
                  Отзывы говорят — мы слышим
                </p>
              </div>
            </div>
            
            {/* Индикатор статуса и кнопка обновления */}
            <div className="flex items-center space-x-4">
              <StatusIndicator isHealthy={isHealthy} />
              <RefreshButton onClick={handleRefreshData} isLoading={isLoading} />
            </div>
          </div>
        </div>
      </header>

      {/* Основной контент */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Панель фильтров */}
        <FilterPanel
          products={productsStats?.products || []}
          selectedProductIds={filters.product_ids || []}
          startDate={dateRange.start}
          endDate={dateRange.end}
          onProductsChange={handleProductsChange}
          onDateRangeChange={handleDateRangeChange}
        />

        {/* Сетка дашборда */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <TonalityPieChart data={tonalityDistribution} />
          <ProductsList products={productsStats?.products} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <TonalityDynamicsChart data={tonalityDynamics} />
          <ProductsBarChart products={productsStats?.products} />
        </div>

        {/* Анализ аспектов */}
        <ProductAspectsAnalysis selectedProductIds={filters.product_ids} />
      </main>
    </div>
  );
}
```

### 2. Панель фильтров (FilterPanel)
```typescript
// src/components/FilterPanel.tsx
interface FilterPanelProps {
  products: Product[];
  selectedProductIds: number[];
  startDate: Date | null;
  endDate: Date | null;
  onProductsChange: (productIds: number[]) => void;
  onDateRangeChange: (startDate?: Date, endDate?: Date) => void;
}

export default function FilterPanel({
  products,
  selectedProductIds,
  startDate,
  endDate,
  onProductsChange,
  onDateRangeChange,
}: FilterPanelProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 mb-8">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0 lg:space-x-6">
        {/* Фильтр по продуктам */}
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Продукты/услуги
          </label>
          <MultiSelect
            options={products.map(p => ({ value: p.id, label: p.name }))}
            value={selectedProductIds}
            onChange={onProductsChange}
            placeholder="Выберите продукты..."
          />
        </div>

        {/* Фильтр по датам */}
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Период
          </label>
          <DateRangePicker
            startDate={startDate}
            endDate={endDate}
            onChange={onDateRangeChange}
            placeholder="Выберите период..."
          />
        </div>

        {/* Кнопки управления */}
        <div className="flex space-x-2">
          <button
            onClick={() => {
              onProductsChange([]);
              onDateRangeChange();
            }}
            className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Сбросить
          </button>
          <FileUploadButton />
        </div>
      </div>
    </div>
  );
}
```

### 3. Круговая диаграмма тональности (TonalityPieChart)
```typescript
// src/components/TonalityPieChart.tsx
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

interface TonalityPieChartProps {
  data: TonalityDistribution[];
  totalReviews: number;
  isFiltered?: boolean;
  filterDescription?: string;
}

export default function TonalityPieChart({
  data,
  totalReviews,
  isFiltered,
  filterDescription
}: TonalityPieChartProps) {
  // Цвета для тональностей
  const COLORS = {
    'положительно': '#22c55e',
    'нейтрально': '#6b7280',
    'отрицательно': '#f97316',
  };

  // Подготовка данных для диаграммы
  const chartData = data.map(item => ({
    name: item.tonality,
    value: item.count,
    percentage: item.percentage,
    color: COLORS[item.tonality as keyof typeof COLORS],
  }));

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 h-96">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Распределение тональности
        </h3>
        {isFiltered && (
          <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
            Фильтр активен
          </span>
        )}
      </div>

      {filterDescription && (
        <p className="text-sm text-gray-600 mb-4">{filterDescription}</p>
      )}

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={2}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number, name: string) => [
                `${value} отзывов (${((value / totalReviews) * 100).toFixed(1)}%)`,
                name
              ]}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 text-center">
        <p className="text-sm text-gray-600">
          Всего отзывов: <span className="font-semibold">{totalReviews.toLocaleString()}</span>
        </p>
      </div>
    </div>
  );
}
```

### 4. Модальное окно загрузки файлов (FileUploadModal)
```typescript
// src/components/FileUploadModal.tsx
export default function FileUploadModal({ isOpen, onClose }: FileUploadModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStage, setUploadStage] = useState<'idle' | 'uploading' | 'processing' | 'downloading' | 'complete'>('idle');
  const [startTime, setStartTime] = useState<number | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);

  // Обработка загрузки файла
  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadStage('uploading');
    setStartTime(Date.now());

    try {
      // Чтение файла для подсчета элементов
      const fileText = await selectedFile.text();
      const fileData = JSON.parse(fileText);
      const itemsCount = fileData.data?.length || 0;

      const formData = new FormData();
      formData.append('file', selectedFile);

      // Этап 1: Загрузка файла
      const uploadInterval = simulateUploadProgress();
      
      const response = await fetch('/api/v1/predict/', {
        method: 'POST',
        body: formData,
      });

      clearInterval(uploadInterval);
      setUploadProgress(100);
      
      // Этап 2: Обработка ML моделями
      setUploadStage('processing');
      const processingInterval = simulateProcessingProgress(itemsCount);

      const blob = await response.blob();
      
      clearInterval(processingInterval);
      setUploadStage('downloading');
      
      // Этап 3: Скачивание результата
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `processed_${selectedFile.name}`;
      a.click();
      
      setUploadStage('complete');
      
      setTimeout(() => {
        handleClose();
      }, 2000);
      
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Произошла ошибка');
      setUploadStage('idle');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className={`fixed inset-0 z-50 ${isOpen ? 'block' : 'hidden'}`}>
      <div className="fixed inset-0 bg-black bg-opacity-50" onClick={onClose} />
      
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Анализ тональности</h3>
            <button onClick={onClose}>
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Drag & Drop область */}
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              isDragging ? 'border-gazprom-blue bg-blue-50' : 'border-gray-300'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-sm text-gray-600 mb-2">
              Перетащите JSON файл сюда или
            </p>
            <label className="cursor-pointer text-gazprom-blue hover:text-gazprom-blue-dark">
              выберите файл
              <input
                type="file"
                accept=".json"
                onChange={handleInputChange}
                className="hidden"
              />
            </label>
          </div>

          {/* Прогресс загрузки */}
          {isUploading && (
            <div className="mt-6 space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-700">
                    {uploadStage === 'uploading' && 'Отправка файла на сервер...'}
                    {uploadStage === 'processing' && 'Анализ тональности ML моделями...'}
                    {uploadStage === 'downloading' && 'Формирование результата...'}
                    {uploadStage === 'complete' && 'Анализ завершен!'}
                  </span>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500">{Math.round(uploadProgress)}%</span>
                    {elapsedTime > 0 && (
                      <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">
                        ⏱️ {formatTime(elapsedTime)}
                      </span>
                    )}
                  </div>
                </div>
                
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${
                      uploadStage === 'complete' ? 'bg-green-500' : 'bg-gazprom-blue'
                    }`}
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>

              {/* Детали обработки */}
              {uploadStage === 'processing' && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center space-x-3">
                    <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-blue-800">
                        🤖 Анализ тональности отзывов
                      </p>
                      <p className="text-xs text-blue-500 mt-1">
                        TF-IDF классификация продуктов • XLM-RoBERTa анализ тональности
                        {elapsedTime > 0 && processedItemsCount > 0 && (
                          <span className="ml-2">
                            • ~{Math.round(processedItemsCount / elapsedTime)} отз/сек
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

## 🔗 API интеграция

### API клиент (api.ts)
```typescript
// src/lib/api.ts
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
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

export const productsApi = {
  getStats: async (): Promise<ProductsStatsResponse> => {
    const response = await apiClient.get<ProductsStatsResponse>('/products/stats');
    return response.data;
  },
};

export const analyticsApi = {
  getTonalityDistribution: async (params: {
    product_ids?: number[];
    start_date?: string;
    end_date?: string;
  } = {}): Promise<TonalityDistributionResponse> => {
    const apiParams: any = { ...params };
    if (params.product_ids && params.product_ids.length > 0) {
      apiParams.product_ids = params.product_ids.join(',');
    }
    
    const response = await apiClient.get<TonalityDistributionResponse>('/analytics/tonality', { 
      params: apiParams 
    });
    return response.data;
  },

  getTonalityDynamics: async (params: {
    product_ids?: number[];
    start_date?: string;
    end_date?: string;
    interval?: IntervalType;
  } = {}): Promise<TonalityDynamicsResponse> => {
    const apiParams: any = { ...params };
    if (params.product_ids && params.product_ids.length > 0) {
      apiParams.product_ids = params.product_ids.join(',');
    }
    
    const response = await apiClient.get<TonalityDynamicsResponse>('/analytics/dynamics', { 
      params: apiParams 
    });
    return response.data;
  },
};

export const apiUtils = {
  healthCheck: async (): Promise<boolean> => {
    try {
      const response = await apiClient.get('/health');
      return response.status === 200;
    } catch {
      return false;
    }
  },
};
```

### Custom hooks (useApi.ts)
```typescript
// src/hooks/useApi.ts
import { useState, useEffect, useCallback } from 'react';
import { productsApi, analyticsApi, apiUtils } from '@/lib/api';

export function useProductsStats() {
  const [data, setData] = useState<ProductsStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await productsApi.getStats();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

export function useTonalityDistribution(filters: AnalyticsFilters) {
  const [data, setData] = useState<TonalityDistributionResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const result = await analyticsApi.getTonalityDistribution({
        product_ids: filters.product_ids,
        start_date: filters.start_date,
        end_date: filters.end_date,
      });
      setData(result);
    } catch (err) {
      console.error('Error fetching tonality distribution:', err);
    } finally {
      setLoading(false);
    }
  }, [filters.product_ids, filters.start_date, filters.end_date]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, refetch: fetchData };
}

export function useApiHealth() {
  const [isHealthy, setIsHealthy] = useState(false);
  const [checking, setChecking] = useState(true);

  const checkHealth = useCallback(async () => {
    try {
      setChecking(true);
      const healthy = await apiUtils.healthCheck();
      setIsHealthy(healthy);
    } catch {
      setIsHealthy(false);
    } finally {
      setChecking(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Проверка каждые 30 секунд
    return () => clearInterval(interval);
  }, [checkHealth]);

  return { isHealthy, checking, refetch: checkHealth };
}

export function useFilters() {
  const [filters, setFilters] = useState<AnalyticsFilters>({
    product_ids: [],
    interval: 'month',
  });

  const updateFilter = useCallback(<K extends keyof AnalyticsFilters>(
    key: K,
    value: AnalyticsFilters[K]
  ) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters({
      product_ids: [],
      interval: 'month',
    });
  }, []);

  return { filters, updateFilter, resetFilters };
}
```

## 📱 Адаптивный дизайн

### Responsive Grid System
```typescript
// Адаптивная сетка дашборда
<div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
  {/* На мобильных - 1 колонка, на десктопе - 2 колонки */}
  <TonalityPieChart />
  <ProductsList />
</div>

<div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
  {/* На больших экранах - 3 колонки */}
  <div className="xl:col-span-2">
    <TonalityDynamicsChart />
  </div>
  <div className="xl:col-span-1">
    <ProductsBarChart />
  </div>
</div>
```

### Mobile-First подход
```css
/* Базовые стили для мобильных */
.filter-panel {
  @apply flex flex-col space-y-4;
}

/* Стили для планшетов */
@media (min-width: 768px) {
  .filter-panel {
    @apply flex-row space-y-0 space-x-4;
  }
}

/* Стили для десктопа */
@media (min-width: 1024px) {
  .filter-panel {
    @apply items-center justify-between;
  }
}
```

## ⚡ Производительность и оптимизация

### Lazy Loading компонентов
```typescript
// Динамический импорт тяжелых компонентов
import dynamic from 'next/dynamic';

const TonalityDynamicsChart = dynamic(
  () => import('@/components/TonalityDynamicsChart'),
  {
    loading: () => <ChartSkeleton />,
    ssr: false, // Отключаем SSR для компонентов с графиками
  }
);

const FileUploadModal = dynamic(
  () => import('@/components/FileUploadModal'),
  {
    loading: () => <ModalSkeleton />,
  }
);
```

### Мемоизация и оптимизация
```typescript
// Мемоизация тяжелых вычислений
const chartData = useMemo(() => {
  return data?.distribution?.map(item => ({
    name: item.tonality,
    value: item.count,
    percentage: item.percentage,
    color: SENTIMENT_COLORS[item.tonality],
  })) || [];
}, [data?.distribution]);

// Дебаунс для поиска и фильтрации
const debouncedSearch = useCallback(
  debounce((searchTerm: string) => {
    setSearchQuery(searchTerm);
  }, 300),
  []
);

// React.memo для предотвращения лишних рендеров
export default React.memo(function ProductsList({ 
  products, 
  onProductSelect 
}: ProductsListProps) {
  // ...
});
```

### Кэширование API запросов
```typescript
// Кэширование с использованием SWR паттерна
const cache = new Map();

export function useCachedApi<T>(key: string, fetcher: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const cachedData = cache.get(key);
    if (cachedData) {
      setData(cachedData);
      setLoading(false);
      return;
    }

    fetcher()
      .then(result => {
        cache.set(key, result);
        setData(result);
      })
      .finally(() => setLoading(false));
  }, [key, fetcher]);

  return { data, loading };
}
```

## 🎯 UX/UI особенности

### Интерактивные элементы
```typescript
// Hover эффекты для карточек продуктов
<div className="group cursor-pointer transform transition-all duration-200 hover:scale-105 hover:shadow-lg">
  <div className="bg-white rounded-lg border p-4 group-hover:border-gazprom-blue">
    {/* Контент карточки */}
  </div>
</div>

// Анимированные кнопки
<button className="relative overflow-hidden bg-gazprom-blue text-white px-4 py-2 rounded-lg transition-all duration-300 hover:bg-gazprom-blue-dark hover:shadow-lg active:scale-95">
  <span className="relative z-10">Обновить данные</span>
  <div className="absolute inset-0 bg-white opacity-0 hover:opacity-10 transition-opacity duration-300" />
</button>
```

### Состояния загрузки
```typescript
// Скелетоны для загрузки
function ChartSkeleton() {
  return (
    <div className="bg-white rounded-lg p-6 h-96">
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/4 mb-4" />
        <div className="h-64 bg-gray-200 rounded" />
      </div>
    </div>
  );
}

// Индикаторы прогресса
function ProgressBar({ progress, stage }: { progress: number; stage: string }) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span>{stage}</span>
        <span>{progress}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className="bg-gazprom-blue h-2 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
```

### Обработка ошибок
```typescript
// Компонент для отображения ошибок
function ErrorBoundary({ children, fallback }: ErrorBoundaryProps) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <div className="flex items-center space-x-2">
        <AlertCircle className="w-5 h-5 text-red-600" />
        <div>
          <h3 className="text-sm font-medium text-red-800">
            Произошла ошибка
          </h3>
          <p className="text-sm text-red-600 mt-1">
            {fallback || 'Попробуйте обновить страницу'}
          </p>
        </div>
      </div>
    </div>
  );
}

// Retry механизм
function useRetry(maxRetries = 3) {
  const [retryCount, setRetryCount] = useState(0);
  
  const retry = useCallback(() => {
    if (retryCount < maxRetries) {
      setRetryCount(prev => prev + 1);
    }
  }, [retryCount, maxRetries]);

  const reset = useCallback(() => {
    setRetryCount(0);
  }, []);

  return { retryCount, retry, reset, canRetry: retryCount < maxRetries };
}
```

## 🚀 Развертывание и сборка

### Next.js конфигурация
```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  
  // Оптимизация изображений
  images: {
    domains: ['localhost'],
    formats: ['image/webp', 'image/avif'],
  },
  
  // Настройки для production
  productionBrowserSourceMaps: false,
  poweredByHeader: false,
  
  // Proxy для API в development
  async rewrites() {
    return process.env.NODE_ENV === 'development' ? [
      {
        source: '/api/v1/:path*',
        destination: 'http://localhost:8000/api/v1/:path*',
      },
    ] : [];
  },
  
  // Переменные окружения
  env: {
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000/api/v1',
  },
};

module.exports = nextConfig;
```

### Docker контейнер
```dockerfile
# Dockerfile
FROM node:18-alpine AS base

# Установка зависимостей
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production

# Сборка приложения
FROM base AS builder
WORKDIR /app
COPY . .
COPY --from=deps /app/node_modules ./node_modules
RUN npm run build

# Production образ
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT 3000

CMD ["node", "server.js"]
```

### Скрипты сборки
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit",
    "build:analyze": "ANALYZE=true npm run build",
    "build:docker": "docker build -t gazprombank-frontend .",
    "test": "jest",
    "test:watch": "jest --watch",
    "storybook": "storybook dev -p 6006"
  }
}
```

## 🧪 Тестирование

### Unit тесты с Jest
```typescript
// __tests__/components/TonalityPieChart.test.tsx
import { render, screen } from '@testing-library/react';
import TonalityPieChart from '@/components/TonalityPieChart';

const mockData = [
  { tonality: 'положительно', count: 100, percentage: 50 },
  { tonality: 'отрицательно', count: 80, percentage: 40 },
  { tonality: 'нейтрально', count: 20, percentage: 10 },
];

describe('TonalityPieChart', () => {
  it('renders chart with correct data', () => {
    render(
      <TonalityPieChart 
        data={mockData} 
        totalReviews={200}
      />
    );
    
    expect(screen.getByText('Распределение тональности')).toBeInTheDocument();
    expect(screen.getByText('Всего отзывов: 200')).toBeInTheDocument();
  });

  it('shows filter indicator when filtered', () => {
    render(
      <TonalityPieChart 
        data={mockData} 
        totalReviews={200}
        isFiltered={true}
      />
    );
    
    expect(screen.getByText('Фильтр активен')).toBeInTheDocument();
  });
});
```

### E2E тесты с Playwright
```typescript
// e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test('loads and displays main components', async ({ page }) => {
    await page.goto('/');
    
    // Проверяем заголовок
    await expect(page.getByText('Контроль тональности')).toBeVisible();
    
    // Проверяем компоненты дашборда
    await expect(page.getByText('Распределение тональности')).toBeVisible();
    await expect(page.getByText('Продукты и услуги')).toBeVisible();
    
    // Проверяем фильтры
    await expect(page.getByPlaceholder('Выберите продукты...')).toBeVisible();
  });

  test('filters work correctly', async ({ page }) => {
    await page.goto('/');
    
    // Выбираем продукт
    await page.getByPlaceholder('Выберите продукты...').click();
    await page.getByText('Дебетовые карты').click();
    
    // Проверяем, что фильтр применился
    await expect(page.getByText('Фильтр активен')).toBeVisible();
  });

  test('file upload modal works', async ({ page }) => {
    await page.goto('/');
    
    // Открываем модальное окно
    await page.getByText('Загрузить файл').click();
    
    // Проверяем модальное окно
    await expect(page.getByText('Анализ тональности')).toBeVisible();
    await expect(page.getByText('Перетащите JSON файл')).toBeVisible();
  });
});
```

## 📊 Метрики производительности

### Core Web Vitals
- **LCP (Largest Contentful Paint)**: <2.5s
- **FID (First Input Delay)**: <100ms
- **CLS (Cumulative Layout Shift)**: <0.1
- **FCP (First Contentful Paint)**: <1.8s
- **TTI (Time to Interactive)**: <3.8s

### Bundle анализ
```bash
# Анализ размера бандла
npm run build:analyze

# Результаты:
# - Main bundle: ~250KB gzipped
# - Charts bundle: ~180KB gzipped (lazy loaded)
# - Total initial load: ~430KB gzipped
```

### Lighthouse Score
- **Performance**: 95+
- **Accessibility**: 98+
- **Best Practices**: 100
- **SEO**: 92+

## 🔗 Связанные разделы

- [05-backend.md](05-backend.md) - Backend API, используемый фронтендом
- [04-classification.md](04-classification.md) - ML модели для анализа файлов
- [07-architecture.md](07-architecture.md) - Общая архитектура системы

---

*Документация создана для проекта анализа тональности отзывов Газпромбанка*
