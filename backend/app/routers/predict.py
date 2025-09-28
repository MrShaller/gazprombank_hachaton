"""
API роутер для обработки загрузки файлов и предсказаний
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
import json
import logging
from typing import Dict, Any, List
from pydantic import ValidationError

from ..schemas import FileUploadData, PredictResponse, ErrorResponse

logger = logging.getLogger(__name__)

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
        
        # ЗАГЛУШКА: Пока что просто возвращаем тот же файл с дополнительными полями
        # В будущем здесь будет обработка ML моделью
        processed_items = []
        for item in validated_data.data:
            processed_item = {
                "id": item.id,
                "text": item.text,
                "predicted_sentiment": "положительно",  # Заглушка
                "confidence": 0.85,  # Заглушка
                "predicted_product": "Общий банковский продукт"  # Заглушка
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
