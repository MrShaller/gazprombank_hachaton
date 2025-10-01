"""
API роутер для обработки загрузки файлов и предсказаний
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
import json
import logging
import sys
import os
import types
from typing import Dict, Any, List
from pydantic import ValidationError

from ..schemas import FileUploadData, PredictResponse, ErrorResponse
from ..ml.pipeline import InferencePipeline
from ..ml.utils import tokenize_lemma

logger = logging.getLogger(__name__)

# Фикс для joblib (ожидает tokenize_lemma в старом месте)
fake_module = types.ModuleType("scripts.models.inference_pipeline")
fake_module.tokenize_lemma = tokenize_lemma
sys.modules["scripts.models.inference_pipeline"] = fake_module

# Дополнительный фикс для __main__
import __main__
__main__.tokenize_lemma = tokenize_lemma

# Инициализация ML пайплайна
try:
    logger.info("Инициализация ML пайплайна...")
    # Определяем корневую папку проекта
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    tfidf_model_path = os.path.join(project_root, "models/tfidf_lr/model.pkl")
    xlmr_model_path = os.path.join(project_root, "models/xlmr")
    
    logger.info(f"Путь к TF-IDF модели: {tfidf_model_path}")
    logger.info(f"Путь к XLM-R модели: {xlmr_model_path}")
    
    ml_pipeline = InferencePipeline(
        tfidf_path=tfidf_model_path,
        xlmr_path=xlmr_model_path
    )
    logger.info("✅ ML пайплайн успешно инициализирован")
except Exception as e:
    logger.error(f"❌ Ошибка инициализации ML пайплайна: {e}")
    ml_pipeline = None

router = APIRouter(prefix="/predict", tags=["predict"])

@router.post("/", response_model=PredictResponse, responses={
    400: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
async def predict_file(file: UploadFile = File(...)):
    """
    Обработка загруженного JSON файла для предсказания тональности
    
    Возвращает структурированный ответ с результатом обработки или ошибками
    """
    try:
        # Проверяем тип файла
        if not file.content_type or "json" not in file.content_type.lower():
            error_response = ErrorResponse(
                message="Поддерживаются только JSON файлы",
                error_code="INVALID_FILE_TYPE",
                details={"content_type": file.content_type, "filename": file.filename}
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response.dict()
            )
        
        # Проверяем размер файла (ограничение 10MB)
        if file.size and file.size > 10 * 1024 * 1024:
            error_response = ErrorResponse(
                message="Размер файла превышает максимально допустимый (10 МБ)",
                error_code="FILE_TOO_LARGE",
                details={"size_mb": round(file.size / 1024 / 1024, 2), "max_size_mb": 10}
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response.dict()
            )
        
        # Читаем содержимое файла
        try:
            content = await file.read()
            if not content:
                error_response = ErrorResponse(
                    message="Загружен пустой файл",
                    error_code="EMPTY_FILE",
                    details={"filename": file.filename}
                )
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=error_response.dict()
                )
        except Exception as e:
            error_response = ErrorResponse(
                message="Ошибка чтения файла",
                error_code="FILE_READ_ERROR",
                details={"error": str(e), "filename": file.filename}
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response.dict()
            )
        
        # Парсим JSON
        try:
            raw_data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            error_response = ErrorResponse(
                message="Ошибка парсинга JSON файла",
                error_code="INVALID_JSON",
                details={
                    "error": str(e),
                    "line": getattr(e, 'lineno', None),
                    "column": getattr(e, 'colno', None),
                    "filename": file.filename
                }
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response.dict()
            )
        except UnicodeDecodeError as e:
            error_response = ErrorResponse(
                message="Ошибка кодировки файла. Используйте UTF-8",
                error_code="ENCODING_ERROR",
                details={"error": str(e), "filename": file.filename}
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response.dict()
            )
        
        # Валидируем структуру данных с помощью Pydantic
        try:
            validated_data = FileUploadData(**raw_data)
        except ValidationError as e:
            validation_errors = []
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                validation_errors.append(f"{field_path}: {error['msg']}")
            
            error_response = ErrorResponse(
                message="Ошибка валидации данных",
                error_code="VALIDATION_ERROR",
                details={
                    "errors": validation_errors,
                    "filename": file.filename,
                    "expected_format": {
                        "data": [
                            {"id": "уникальный_идентификатор", "text": "текст_для_анализа"}
                        ]
                    }
                }
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=error_response.dict()
            )
        
        # Дополнительные проверки данных
        validation_errors = []
        for i, item in enumerate(validated_data.data):
            if not item.text.strip():
                validation_errors.append(f"Элемент {i}: поле 'text' не может быть пустым")
            if len(item.text.strip()) < 3:
                validation_errors.append(f"Элемент {i}: поле 'text' слишком короткое (минимум 3 символа)")
        
        if validation_errors:
            error_response = ErrorResponse(
                message="Найдены ошибки в данных",
                error_code="DATA_VALIDATION_ERROR",
                details={
                    "errors": validation_errors,
                    "filename": file.filename
                }
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=error_response.dict()
            )
        
        logger.info(f"Получен валидный файл {file.filename} с {len(validated_data.data)} записями")
        
        # Проверяем статус ML пайплайна
        if ml_pipeline is None:
            logger.warning("ML пайплайн не инициализирован")
        else:
            logger.info("ML пайплайн доступен, начинаем обработку")
        
        # Обработка ML моделями
        if ml_pipeline is None:
            # Fallback на заглушку, если ML пайплайн не инициализирован
            logger.warning("ML пайплайн недоступен, используется заглушка")
            processed_items = []
            for item in validated_data.data:
                processed_item = {
                    "id": item.id,
                    "text": item.text,
                    "predicted_sentiment": "нейтрально",
                    "confidence": 0.0,
                    "predicted_products": ["Общий банковский продукт"],
                    "error": "ML модели недоступны"
                }
                processed_items.append(processed_item)
        else:
            try:
                # Подготавливаем данные для ML пайплайна
                input_data = [{"id": item.id, "text": item.text} for item in validated_data.data]
                
                # Запускаем ML пайплайн с агрегацией
                df_results = ml_pipeline.run_and_aggregate_from_json(input_data)
                
                # Обрабатываем результаты ML пайплайна
                processed_items = []
                for review_id in df_results['review_id'].unique():
                    review_data = df_results[df_results['review_id'] == review_id].iloc[0]
                    
                    # Извлекаем предсказания BERT (тональность по продуктам)
                    bert_predictions = review_data.get('pred_agg', {})
                    if isinstance(bert_predictions, dict) and bert_predictions:
                        # Берем наиболее частую тональность
                        sentiments = list(bert_predictions.values())
                        predicted_sentiment = max(set(sentiments), key=sentiments.count) if sentiments else "нейтрально"
                        predicted_products = list(bert_predictions.keys())
                        confidence = len([s for s in sentiments if s == predicted_sentiment]) / len(sentiments) if sentiments else 0.0
                    else:
                        predicted_sentiment = "нейтрально"
                        predicted_products = []
                        confidence = 0.0
                    
                    # Добавляем TF-IDF предсказания как дополнительные продукты
                    tfidf_predictions = review_data.get('pred_tfidf_agg', [])
                    if isinstance(tfidf_predictions, list):
                        predicted_products.extend(tfidf_predictions)
                    
                    # Убираем дубликаты и пустые значения
                    predicted_products = list(set([p for p in predicted_products if p and p.strip()]))
                    if not predicted_products:
                        predicted_products = ["Общий банковский продукт"]
                    
                    # Находим оригинальный текст
                    original_item = next((item for item in validated_data.data if str(item.id) == str(review_id)), None)
                    original_text = original_item.text if original_item else ""
                    
                    processed_item = {
                        "id": int(review_id),  # Конвертируем numpy.int64 в int
                        "text": str(original_text),
                        "predicted_sentiment": str(predicted_sentiment),
                        "confidence": float(round(confidence, 3)),
                        "predicted_products": [str(p) for p in predicted_products[:5]],  # Ограничиваем до 5 продуктов
                        "bert_details": {str(k): str(v) for k, v in bert_predictions.items()} if isinstance(bert_predictions, dict) else {},
                        "tfidf_products": [str(p) for p in tfidf_predictions] if isinstance(tfidf_predictions, list) else []
                    }
                    processed_items.append(processed_item)
                
                logger.info(f"ML обработка завершена для {len(processed_items)} отзывов")
                
            except Exception as e:
                logger.error(f"Ошибка ML обработки: {e}")
                # Fallback на заглушку при ошибке ML
                processed_items = []
                for item in validated_data.data:
                    processed_item = {
                        "id": int(item.id) if hasattr(item.id, 'item') else item.id,
                        "text": str(item.text),
                        "predicted_sentiment": "нейтрально",
                        "confidence": 0.0,
                        "predicted_products": ["Общий банковский продукт"],
                        "error": f"Ошибка ML обработки: {str(e)}"
                    }
                    processed_items.append(processed_item)
        
        response = PredictResponse(
            success=True,
            message="Файл успешно обработан",
            data=processed_items,
            total_items=len(processed_items)
        )
        
        return JSONResponse(
            content=response.dict(),
            headers={
                "Content-Disposition": f"attachment; filename=processed_{file.filename}"
            }
        )
        
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обработке файла {file.filename}: {str(e)}")
        error_response = ErrorResponse(
            message="Внутренняя ошибка сервера",
            error_code="INTERNAL_ERROR",
            details={"filename": file.filename}
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.dict()
        )

@router.get("/health")
async def predict_health():
    """Проверка работоспособности сервиса предсказаний"""
    return {"status": "ok", "service": "predict"}
