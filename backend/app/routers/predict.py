"""
API роутер для обработки загрузки файлов и предсказаний
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predict", tags=["predict"])

@router.post("/")
async def predict_file(file: UploadFile = File(...)):
    """
    Обработка загруженного JSON файла для предсказания тональности
    
    Пока что это заглушка, которая просто возвращает загруженный файл
    """
    try:
        # Проверяем тип файла
        if not file.content_type or "json" not in file.content_type.lower():
            raise HTTPException(
                status_code=400,
                detail="Поддерживаются только JSON файлы"
            )
        
        # Читаем содержимое файла
        content = await file.read()
        
        try:
            # Парсим JSON
            data = json.loads(content.decode('utf-8'))
            
            # Валидируем структуру
            if "data" not in data:
                raise HTTPException(
                    status_code=400,
                    detail="JSON должен содержать поле 'data'"
                )
            
            if not isinstance(data["data"], list):
                raise HTTPException(
                    status_code=400,
                    detail="Поле 'data' должно быть массивом"
                )
            
            # Проверяем структуру элементов
            for i, item in enumerate(data["data"]):
                if not isinstance(item, dict):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Элемент {i} в 'data' должен быть объектом"
                    )
                
                if "id" not in item or "text" not in item:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Элемент {i} должен содержать поля 'id' и 'text'"
                    )
            
            logger.info(f"Получен файл {file.filename} с {len(data['data'])} записями")
            
            # ЗАГЛУШКА: Пока что просто возвращаем тот же файл
            # В будущем здесь будет обработка ML моделью
            processed_data = {
                "data": data["data"],
                "processed": True,
                "total_items": len(data["data"]),
                "message": "Файл успешно обработан (заглушка)"
            }
            
            return JSONResponse(
                content=processed_data,
                headers={
                    "Content-Disposition": f"attachment; filename=processed_{file.filename}"
                }
            )
            
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка парсинга JSON: {str(e)}"
            )
            
    except Exception as e:
        logger.error(f"Ошибка обработки файла {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка обработки файла: {str(e)}"
        )

@router.get("/health")
async def predict_health():
    """Проверка работоспособности сервиса предсказаний"""
    return {"status": "ok", "service": "predict"}
