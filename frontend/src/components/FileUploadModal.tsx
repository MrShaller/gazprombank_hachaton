/**
 * Модальное окно для загрузки JSON файлов
 */
'use client';

import React, { useState, useCallback } from 'react';
import { X, Upload, AlertCircle } from 'lucide-react';

interface FileUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function FileUploadModal({ isOpen, onClose }: FileUploadModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  // Загрузка файла на сервер
  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('/api/v1/predict', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Ошибка загрузки: ${response.statusText}`);
      }

      // Пока что просто скачиваем обратно тот же файл (заглушка)
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `processed_${selectedFile.name}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      // Закрываем модальное окно и сбрасываем состояние
      handleClose();
    } catch (err) {
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

        {/* Ошибка */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Кнопки */}
        <div className="flex justify-end space-x-3 mt-6">
          <button
            onClick={handleClose}
            disabled={isUploading}
            className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50"
          >
            Отмена
          </button>
          <button
            onClick={handleUpload}
            disabled={!selectedFile || isUploading}
            className="px-6 py-2 bg-gazprom-blue text-white rounded-lg hover:bg-gazprom-blue-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isUploading ? 'Загружается...' : 'Загрузить'}
          </button>
        </div>
      </div>
    </div>
  );
}
