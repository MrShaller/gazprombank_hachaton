/**
 * Модальное окно для загрузки JSON файлов
 */
'use client';

import React, { useState, useCallback } from 'react';
import { X, Upload, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

interface FileUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function FileUploadModal({ isOpen, onClose }: FileUploadModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStage, setUploadStage] = useState<'idle' | 'uploading' | 'processing' | 'downloading' | 'complete'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [processedItemsCount, setProcessedItemsCount] = useState(0);
  const [totalItemsCount, setTotalItemsCount] = useState(0);
  const [startTime, setStartTime] = useState<number | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);

  // Форматирование времени
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins > 0) {
      return `${mins}м ${secs}с`;
    }
    return `${secs}с`;
  };

  // Эффект для обновления таймера
  React.useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    
    if (isUploading && startTime) {
      interval = setInterval(() => {
        const now = Date.now();
        const elapsed = Math.floor((now - startTime) / 1000);
        setElapsedTime(elapsed);
      }, 1000);
    }

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [isUploading, startTime]);

  // Обработка выбора файла
  const handleFileSelect = useCallback((file: File) => {
    if (file.type !== 'application/json') {
      setError('Пожалуйста, выберите JSON файл');
      return;
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB
      setError('Размер файла не должен превышать 10 МБ');
      return;
    }

    setSelectedFile(file);
    setError(null);
  }, []);

  // Обработка drag & drop
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  // Обработка выбора через input
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  // Симуляция прогресса загрузки
  const simulateUploadProgress = () => {
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 95) {
          clearInterval(interval);
          return 95; // Останавливаемся на 95%, ждем ответа сервера
        }
        // Замедляем прогресс по мере приближения к концу
        const increment = prev < 50 ? Math.floor(Math.random() * 8) + 3 : 
                         prev < 80 ? Math.floor(Math.random() * 4) + 2 : 
                         Math.floor(Math.random() * 2) + 1;
        return Math.min(prev + increment, 95);
      });
    }, 200);
    return interval;
  };

  // Симуляция прогресса обработки
  const simulateProcessingProgress = (totalItems: number) => {
    setTotalItemsCount(totalItems);
    setProcessedItemsCount(0);
    
    const interval = setInterval(() => {
      setProcessedItemsCount(prev => {
        const next = prev + Math.floor(Math.random() * 3) + 1;
        if (next >= totalItems) {
          clearInterval(interval);
          return totalItems;
        }
        return next;
      });
    }, 200);
    
    return interval;
  };

  // Загрузка файла на сервер
  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setError(null);
    setUploadProgress(0);
    setUploadStage('uploading');
    setStartTime(Date.now());
    setElapsedTime(0);

    let uploadInterval: NodeJS.Timeout | null = null;
    let processingInterval: NodeJS.Timeout | null = null;

    try {
      // Читаем файл для подсчета элементов
      const fileText = await selectedFile.text();
      const fileData = JSON.parse(fileText);
      const itemsCount = fileData.data?.length || 0;

      const formData = new FormData();
      formData.append('file', selectedFile);

      // Этап 1: Загрузка файла с анимированным прогрессом
      setUploadStage('uploading');
      uploadInterval = simulateUploadProgress();

      // Запускаем запрос
      const response = await fetch('/api/v1/predict/', {
        method: 'POST',
        body: formData,
      });

      // Останавливаем симуляцию загрузки и переходим к обработке
      if (uploadInterval) {
        clearInterval(uploadInterval);
      }
      
      setUploadProgress(100); // Завершаем этап загрузки
      
      // Небольшая пауза для визуального эффекта
      await new Promise(resolve => setTimeout(resolve, 300));

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Ошибка загрузки: ${response.status} ${response.statusText}\n${errorText}`);
      }

      // Этап 2: Обработка ML моделями
      setUploadStage('processing');
      setUploadProgress(10);
      
      // Симулируем прогресс обработки
      processingInterval = simulateProcessingProgress(itemsCount);

      // Постепенно увеличиваем общий прогресс во время получения данных
      const processingProgressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 85) {
            clearInterval(processingProgressInterval);
            return 85;
          }
          return prev + Math.floor(Math.random() * 3) + 1;
        });
      }, 300);

      // Получаем результат (это может занять время для больших файлов)
      const blob = await response.blob();
      
      // Останавливаем все интервалы
      if (processingInterval) {
        clearInterval(processingInterval);
      }
      clearInterval(processingProgressInterval);
      
      setUploadStage('downloading');
      setUploadProgress(95);
      
      // Финальный этап
      setTimeout(() => {
        setUploadProgress(100);
        setUploadStage('complete');
        
        // Скачиваем обработанный файл
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `processed_${selectedFile.name}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        // Показываем успех на 2 секунды, затем закрываем
        setTimeout(() => {
          handleClose();
        }, 2000);
      }, 500);
      
    } catch (err) {
      // Очищаем все интервалы при ошибке
      if (uploadInterval) clearInterval(uploadInterval);
      if (processingInterval) clearInterval(processingInterval);
      
      setUploadStage('idle');
      setError(err instanceof Error ? err.message : 'Произошла ошибка при загрузке');
    } finally {
      setIsUploading(false);
    }
  };

  // Закрытие модального окна
  const handleClose = () => {
    setSelectedFile(null);
    setError(null);
    setIsDragging(false);
    setIsUploading(false);
    setUploadProgress(0);
    setUploadStage('idle');
    setProcessedItemsCount(0);
    setTotalItemsCount(0);
    setStartTime(null);
    setElapsedTime(0);
    onClose();
  };

  // Обработка Escape
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleClose();
    }
  }, []);

  // Подключаем обработчик Escape
  React.useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, handleKeyDown]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      onClick={handleClose}
    >
      <div 
        className="bg-white rounded-lg w-full max-w-2xl mx-4 p-6 relative"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Заголовок */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">
            Выберите файл для загрузки
          </h2>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        {/* Информация о формате */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-2">
                Формат входных запросов в файле должен быть представлен в данном виде:
              </p>
              <pre className="bg-blue-100 p-3 rounded text-xs overflow-x-auto whitespace-pre-wrap break-words">
{`{
  "data": [
    {"id": 1, "text": "Очень понравилось обслуживание в отделении, но мобильное приложение часто зависает."},
    {"id": 2, "text": "Кредитную карту одобрили быстро, но лимит слишком маленький."}
  ]
}`}
              </pre>
            </div>
          </div>
        </div>

        {/* Область загрузки */}
        <div
          className={`
            border-2 border-dashed rounded-lg p-8 text-center transition-colors
            ${isDragging 
              ? 'border-gazprom-blue bg-blue-50' 
              : selectedFile 
              ? 'border-green-300 bg-green-50' 
              : 'border-gray-300 hover:border-gray-400'
            }
          `}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {selectedFile ? (
            <div className="space-y-2">
              <div className="text-green-600">
                <Upload className="w-8 h-8 mx-auto mb-2" />
              </div>
              <p className="text-sm font-medium text-gray-900">
                {selectedFile.name}
              </p>
              <p className="text-xs text-gray-600">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} МБ
              </p>
              <button
                onClick={() => setSelectedFile(null)}
                className="text-xs text-gray-500 hover:text-gray-700"
              >
                Выбрать другой файл
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <Upload className="w-8 h-8 mx-auto text-gray-400" />
              <p className="text-sm text-gray-600">
                Перетащите JSON файл сюда или{' '}
                <label className="text-gazprom-blue hover:text-gazprom-blue-dark cursor-pointer">
                  выберите файл
                  <input
                    type="file"
                    accept=".json,application/json"
                    onChange={handleInputChange}
                    className="hidden"
                  />
                </label>
              </p>
              <p className="text-xs text-gray-500">
                Максимальный размер: 10 МБ
              </p>
            </div>
          )}
        </div>

        {/* Прогресс загрузки */}
        {isUploading && (
          <div className="mt-6 space-y-4">
            {/* Общий прогрессбар */}
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
                  {isUploading && elapsedTime > 0 && (
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
            {uploadStage === 'processing' && totalItemsCount > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-blue-800">
                      🤖 Анализ тональности отзывов
                    </p>
                    <div className="flex justify-between items-center mt-1">
                      <p className="text-xs text-blue-600">
                        Обработано {processedItemsCount} из {totalItemsCount} отзывов
                      </p>
                      {elapsedTime > 0 && (
                        <span className="text-xs text-blue-400 bg-blue-100 px-2 py-0.5 rounded">
                          {formatTime(elapsedTime)}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-blue-500 mt-1">
                      TF-IDF классификация продуктов • XLM-RoBERTa анализ тональности
                      {elapsedTime > 0 && processedItemsCount > 0 && (
                        <span className="ml-2">
                          • ~{Math.round(processedItemsCount / elapsedTime)} отз/сек
                        </span>
                      )}
                    </p>
                    <div className="mt-2 w-full bg-blue-200 rounded-full h-1.5">
                      <div 
                        className="h-1.5 bg-blue-500 rounded-full transition-all duration-200"
                        style={{ width: `${Math.min((processedItemsCount / totalItemsCount) * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Детали загрузки */}
            {uploadStage === 'uploading' && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <Loader2 className="w-5 h-5 text-gray-600 animate-spin" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-800">
                      {uploadProgress < 95 ? '📤 Отправка данных на сервер' : '⏳ Ожидание ответа сервера'}
                    </p>
                    <p className="text-xs text-gray-600 mt-1">
                      Файл: {selectedFile?.name} ({((selectedFile?.size || 0) / 1024 / 1024).toFixed(2)} МБ)
                    </p>
                    {uploadProgress >= 95 && (
                      <p className="text-xs text-gray-500 mt-1">
                        Сервер обрабатывает запрос...
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Детали финализации */}
            {uploadStage === 'downloading' && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <Loader2 className="w-5 h-5 text-green-600 animate-spin" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-green-800">
                      📊 Подготовка результатов
                    </p>
                    <p className="text-xs text-green-600 mt-1">
                      Формирование JSON с результатами анализа...
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Успешное завершение */}
            {uploadStage === 'complete' && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-green-800">
                      ✅ Анализ тональности завершен!
                    </p>
                    <div className="flex justify-between items-center mt-1">
                      <p className="text-xs text-green-600">
                        Обработано {totalItemsCount} отзывов • Результат скачивается автоматически
                      </p>
                      {elapsedTime > 0 && (
                        <span className="text-xs text-green-500 bg-green-100 px-2 py-0.5 rounded font-medium">
                          🎯 {formatTime(elapsedTime)}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-green-500 mt-1">
                      Окно закроется через несколько секунд
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Ошибка */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700 whitespace-pre-wrap">{error}</p>
          </div>
        )}

        {/* Кнопки */}
        <div className="flex justify-end space-x-3 mt-6">
          <button
            onClick={handleClose}
            disabled={isUploading && uploadStage !== 'complete'}
            className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50"
          >
            {uploadStage === 'complete' ? 'Закрыть' : 'Отмена'}
          </button>
          <button
            onClick={handleUpload}
            disabled={!selectedFile || isUploading}
            className="px-6 py-2 bg-gazprom-blue text-white rounded-lg hover:bg-gazprom-blue-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isUploading && uploadStage !== 'complete' && (
              <Loader2 className="w-4 h-4 animate-spin" />
            )}
            {uploadStage === 'complete' && (
              <CheckCircle className="w-4 h-4" />
            )}
            <span>
              {uploadStage === 'uploading' && 'Отправка...'}
              {uploadStage === 'processing' && 'Анализ ML...'}
              {uploadStage === 'downloading' && 'Завершение...'}
              {uploadStage === 'complete' && 'Готово!'}
              {uploadStage === 'idle' && 'Начать анализ'}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
