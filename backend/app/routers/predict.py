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

from ..schemas import FileUploadData, PredictResponse, ErrorResponse
from ..ml.pipeline import InferencePipeline
from ..ml.utils import tokenize_lemma
from pathlib import Path
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
        # Проверяем, что действительно загружен файл, а не текст
        if not file.filename:
            error_response = ErrorResponse(
                message="Необходимо загрузить файл, а не отправлять текст в теле запроса",
                error_code="NO_FILE_UPLOADED",
                details={
                    "explanation": "Этот endpoint ожидает файл в формате multipart/form-data",
                    "correct_usage": "curl -X POST 'http://itsfour-solution.ru/api/v1/predict/' -F 'file=@reviews.json'",
                    "file_format": {
                        "required_format": "JSON",
                        "structure": {
                            "data": [
                                {"id": 1, "text": "Текст отзыва для анализа"},
                                {"id": 2, "text": "Еще один отзыв"}
                            ]
                        }
                    },
                    "note": "Убедитесь, что вы загружаете файл с помощью параметра 'file=@filename.json'"
                }
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response.dict()
            )
        
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
        
        # Дополнительная проверка на случай отправки текста вместо файла
        if file.size and file.size < 10:  # Слишком маленький размер может указывать на текст
            error_response = ErrorResponse(
                message="Файл слишком мал или содержит недостаточно данных",
                error_code="FILE_TOO_SMALL",
                details={
                    "size_bytes": file.size,
                    "explanation": "Возможно, вы отправляете текст вместо файла",
                    "correct_usage": "curl -X POST 'http://itsfour-solution.ru/api/v1/predict/' -F 'file=@reviews.json'",
                    "minimum_file_structure": {
                        "data": [{"id": 1, "text": "Минимальный пример отзыва"}]
                    }
                }
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
                message="Ошибка парсинга JSON файла - возможно, вы отправили текст вместо файла",
                error_code="INVALID_JSON",
                details={
                    "error": str(e),
                    "line": getattr(e, 'lineno', None),
                    "column": getattr(e, 'colno', None),
                    "filename": file.filename,
                    "explanation": "Убедитесь, что вы загружаете корректный JSON файл, а не отправляете текст в теле запроса",
                    "correct_usage": "curl -X POST 'http://itsfour-solution.ru/api/v1/predict/' -F 'file=@reviews.json'",
                    "required_json_structure": {
                        "data": [
                            {"id": 1, "text": "Текст первого отзыва"},
                            {"id": 2, "text": "Текст второго отзыва"}
                        ]
                    },
                    "common_mistakes": [
                        "Отправка текста в теле запроса вместо файла",
                        "Использование неправильного Content-Type",
                        "Некорректный JSON синтаксис в файле"
                    ]
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
        
        processed_items = []

        # Инициализируем/получаем ML пайплайн
        pipeline = get_pipeline()
        if pipeline is None:
            logger.warning("ML пайплайн не инициализирован, будет использоваться заглушка")
        else:
            logger.info("ML пайплайн доступен, начинаем обработку")
        
        if pipeline is None:
            # Fallback на заглушку, если ML пайплайн не инициализирован
            logger.warning("ML пайплайн недоступен, используется заглушка")
            for item in validated_data.data:
                processed_items.append({
                    "id": item.id,
                    "text": item.text,
                    "predicted_sentiment": "нейтрально",
                    "confidence": 0.0,
                    "predicted_products": ["Общий банковский продукт"],
                    "error": "ML модели недоступны"
                })
        else:
            try:
                # Подготавливаем данные для ML пайплайна
                input_data = [{"id": item.id, "text": item.text} for item in validated_data.data]
                
                # Запускаем ML пайплайн с агрегацией
                df_results = pipeline.run_and_aggregate_from_json(input_data)
                
                # Обрабатываем результаты ML пайплайна
                for review_id in df_results['review_id'].unique():
                    review_data = df_results[df_results['review_id'] == review_id].iloc[0]
                    
                    # Извлекаем предсказания BERT (тональность по продуктам)
                    bert_map = review_data.get('pred_agg_rules') or review_data.get('pred_agg') or {}
                    if isinstance(bert_map, dict) and bert_map:
                        sentiments = list(bert_map.values())
                        predicted_sentiment = max(set(sentiments), key=sentiments.count) if sentiments else "нейтрально"
                        predicted_products = list(bert_map.keys())
                        confidence = len([s for s in sentiments if s == predicted_sentiment]) / len(sentiments) if sentiments else 0.0
                    else:
                        predicted_sentiment = "нейтрально"
                        predicted_products = []
                        confidence = 0.0

                    # Добавляем TF-IDF предсказания как дополнительные темы
                    tfidf_predictions = review_data.get('pred_tfidf_agg', [])
                    if isinstance(tfidf_predictions, list):
                        predicted_products.extend(tfidf_predictions)
                    
                    # Если ничего не найдено, используем заглушку
                    predicted_products = list({p for p in predicted_products if p and str(p).strip()})
                    if not predicted_products:
                        predicted_products = ["Общий банковский продукт"]
                    
                    # Ограничиваем количество тем (максимум 5)
                    # Оригинальный текст
                    original_item = next((item for item in validated_data.data if str(item.id) == str(review_id)), None)
                    original_text = original_item.text if original_item else ""

                    processed_items.append({
                        "id": int(review_id),
                        "text": str(original_text),
                        "predicted_sentiment": str(predicted_sentiment),
                        "confidence": float(round(confidence, 3)),
                        "predicted_products": [str(p) for p in predicted_products[:5]],
                        "bert_details": {str(k): str(v) for k, v in bert_map.items()} if isinstance(bert_map, dict) else {},
                        "tfidf_products": [str(p) for p in tfidf_predictions] if isinstance(tfidf_predictions, list) else []
                    })
                
                logger.info(f"ML обработка завершена для {len(processed_items)} отзывов")
                
            except Exception as e:
                logger.error(f"Ошибка ML обработки: {e}")
                # Fallback на заглушку при ошибке ML
                for item in validated_data.data:
                    processed_items.append({
                        "id": item.id,
                        "text": item.text,
                        "predicted_sentiment": "нейтрально",
                        "confidence": 0.0,
                        "predicted_products": ["Общий банковский продукт"],
                        "error": f"Ошибка ML обработки: {str(e)}"
                    })
        
        # вместо response = PredictResponse(...)
        predictions = []
        for item in processed_items:
            topics = []
            sentiments = []

            # 1) если есть bert_details — извлекаем темы и тональности
            if "bert_details" in item and isinstance(item["bert_details"], dict):
                for topic, sentiment in item["bert_details"].items():
                    topics.append(str(topic))
                    sentiments.append(str(sentiment))

            # 2) добавляем TF-IDF продукты как отдельные темы (тональность по ним не предсказывается, можно ставить "нейтрально" или пропускать)
            if "tfidf_products" in item and isinstance(item["tfidf_products"], list):
                for topic in item["tfidf_products"]:
                    if topic not in topics:
                        topics.append(str(topic))
                        sentiments.append("нейтрально")

            # fallback — если нет тем, добавляем заглушку
            if not topics:
                topics = ["Общий банковский продукт"]
                sentiments = ["нейтрально"]

            predictions.append({
                "id": item["id"],
                "topics": topics,
                "sentiments": sentiments
            })

        return JSONResponse(content={"predictions": predictions})
        
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
