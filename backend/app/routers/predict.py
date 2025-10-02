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
import asyncio
import threading
from pydantic import ValidationError

from ..schemas import FileUploadData, PredictResponse, ErrorResponse, PredictionItem
from ..ml.pipeline import InferencePipeline
from ..ml.utils import tokenize_lemma
from pathlib import Path
import os
import time
import time

MODELS_DIR = Path(os.getenv("MODELS_PATH", "/app/models"))
ml_pipeline = None  # глобальная ссылка на ML пайплайн
_pipeline_lock = threading.Lock()


logger = logging.getLogger(__name__)

# Фикс для joblib (ожидает tokenize_lemma в старом месте)
fake_module = types.ModuleType("scripts.models.inference_pipeline")
fake_module.tokenize_lemma = tokenize_lemma
sys.modules["scripts.models.inference_pipeline"] = fake_module

# Дополнительный фикс для __main__
import __main__
__main__.tokenize_lemma = tokenize_lemma

def get_pipeline() -> InferencePipeline | None:
    global ml_pipeline
    if ml_pipeline is not None:
        return ml_pipeline
    # Потокобезопасная одноразовая инициализация
    with _pipeline_lock:
        if ml_pipeline is not None:
            return ml_pipeline
        try:
            logger.info("Инициализация ML пайплайна...")
            ml_pipeline_local = InferencePipeline(
                tfidf_path=MODELS_DIR / "tfidf_lr/model.pkl",
                xlmr_path=MODELS_DIR / "xlmr"
            )
            ml_pipeline = ml_pipeline_local
            logger.info("✅ ML пайплайн успешно инициализирован")
            ml_pipeline = ml_pipeline_local
            logger.info("✅ ML пайплайн успешно инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации ML пайплайна: {e}")
            ml_pipeline = None
        return ml_pipeline

router = APIRouter(tags=["predict"])

@router.post("", response_model=PredictResponse, responses={
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
        
        predictions = []

        # Инициализируем/получаем ML пайплайн
        pipeline = get_pipeline()
        if pipeline is None:
            logger.warning("ML пайплайн не инициализирован, будет использоваться заглушка")
        else:
            logger.info("ML пайплайн доступен, начинаем обработку")
        
        if ml_pipeline is None:
            # Fallback на заглушку, если ML пайплайн не инициализирован
            logger.warning("ML пайплайн недоступен, используется заглушка")
            for item in validated_data.data:
                prediction = PredictionItem(
                    id=item.id,
                    topics=["Общий банковский продукт"],
                    sentiments=["нейтрально"]
                )
                predictions.append(prediction)
        else:
            try:
                # Подготавливаем данные для ML пайплайна
                input_data = [{"id": item.id, "text": item.text} for item in validated_data.data]
                
                # Запускаем ML пайплайн с агрегацией
                df_results = ml_pipeline.run_and_aggregate_from_json(input_data)
                
                # Обрабатываем результаты ML пайплайна
                for review_id in df_results['review_id'].unique():
                    review_data = df_results[df_results['review_id'] == review_id].iloc[0]
                    
                    # Извлекаем предсказания BERT (тональность по продуктам)
                    bert_predictions = review_data.get('pred_agg', {})
                    topics = []
                    sentiments = []
                    
                    if isinstance(bert_predictions, dict) and bert_predictions:
                        # Извлекаем темы и тональности из BERT
                        for topic, sentiment in bert_predictions.items():
                            if topic and topic.strip():
                                topics.append(str(topic))
                                sentiments.append(str(sentiment))
                    
                    # Добавляем TF-IDF предсказания как дополнительные темы
                    tfidf_predictions = review_data.get('pred_tfidf_agg', [])
                    if isinstance(tfidf_predictions, list):
                        for tfidf_topic in tfidf_predictions:
                            if tfidf_topic and tfidf_topic.strip() and tfidf_topic not in topics:
                                topics.append(str(tfidf_topic))
                                sentiments.append("нейтрально")  # Для TF-IDF тем используем нейтральную тональность
                    
                    # Если ничего не найдено, используем заглушку
                    if not topics:
                        topics = ["Общий банковский продукт"]
                        sentiments = ["нейтрально"]
                    
                    # Ограничиваем количество тем (максимум 5)
                    if len(topics) > 5:
                        topics = topics[:5]
                        sentiments = sentiments[:5]
                    
                    prediction = PredictionItem(
                        id=review_id,
                        topics=topics,
                        sentiments=sentiments
                    )
                    predictions.append(prediction)
                
                logger.info(f"ML обработка завершена для {len(predictions)} отзывов")
                
            except Exception as e:
                logger.error(f"Ошибка ML обработки: {e}")
                # Fallback на заглушку при ошибке ML
                for item in validated_data.data:
                    prediction = PredictionItem(
                        id=item.id,
                        topics=["Общий банковский продукт"],
                        sentiments=["нейтрально"]
                    )
                    predictions.append(prediction)
        
        response = PredictResponse(predictions=predictions)
        
        
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