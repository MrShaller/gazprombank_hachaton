#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки работы с Ollama

Проверяет доступность Ollama и модели, тестирует разметку на нескольких примерах.
"""

import subprocess
import json
import time
from label_clauses_ollama import OllamaClauseLabeler
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_ollama():
    """Проверка доступности Ollama"""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info("✅ Ollama доступна")
            logger.info("Установленные модели:")
            logger.info(result.stdout)
            return True
        else:
            logger.error("❌ Ollama недоступна")
            return False
    except FileNotFoundError:
        logger.error("❌ Ollama не установлена")
        return False
    except subprocess.TimeoutExpired:
        logger.error("❌ Timeout при проверке Ollama")
        return False

def test_model(model_name: str = "llama3.1:8b-instruct-q8_0"):
    """Тестирование модели на простом примере"""
    try:
        logger.info(f"Тестируем модель {model_name}...")
        
        test_prompt = "Привет! Ответь коротко: сколько будет 2+2?"
        
        result = subprocess.run(
            ['ollama', 'run', model_name],
            input=test_prompt,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info("✅ Модель отвечает:")
            logger.info(f"Ответ: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"❌ Ошибка модели: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Timeout при тестировании модели")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        return False

def test_clause_labeling():
    """Тестирование разметки клауз"""
    test_cases = [
        {
            "clause": "Очень понравилось обслуживание в отделении, сотрудники вежливые и компетентные.",
            "context": "Пришел в банк решать вопрос с кредитом. Очень понравилось обслуживание в отделении, сотрудники вежливые и компетентные. Все быстро оформили, без лишних вопросов."
        },
        {
            "clause": "Мобильное приложение постоянно зависает, невозможно пользоваться!",
            "context": "Скачал мобильное приложение банка для удобства. Мобильное приложение постоянно зависает, невозможно пользоваться! Приходится идти в отделение."
        },
        {
            "clause": "Взял автокредит под 12%, условия нормальные, одобрили быстро.",
            "context": "Нужна была машина срочно. Взял автокредит под 12%, условия нормальные, одобрили быстро. В целом доволен."
        },
        {
            "clause": "Комиссия за обслуживание карты слишком высокая.",
            "context": "Пользуюсь дебетовой картой уже год. Комиссия за обслуживание карты слишком высокая. Думаю закрывать счет и переходить в другой банк."
        },
        {
            "clause": "Вклад открыл на год под 8%.",
            "context": "Решил открыть депозит для накоплений. Вклад открыл на год под 8%. Пока доволен процентной ставкой."
        }
    ]
    
    try:
        logger.info("Тестируем разметку клауз...")
        labeler = OllamaClauseLabeler()
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n--- Тест {i}/5 ---")
            logger.info(f"Клауза: {test_case['clause']}")
            logger.info(f"Контекст: {test_case['context'][:100]}...")
            
            start_time = time.time()
            
            # Создаем промпт с контекстом
            prompt = labeler.create_prompt(test_case['clause'], test_case['context'])
            
            # Получаем ответ от модели
            llm_response = labeler.call_ollama(prompt)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            logger.info(f"Результат: {llm_response['topics']} | {llm_response['sentiments']}")
            logger.info(f"Равное количество: {len(llm_response['topics']) == len(llm_response['sentiments'])}")
            logger.info(f"Время обработки: {processing_time:.2f} сек")
        
        logger.info("\n✅ Тестирование разметки завершено успешно")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании разметки: {e}")
        return False

def main():
    """Основная функция тестирования"""
    logger.info("🧪 ТЕСТИРОВАНИЕ СИСТЕМЫ РАЗМЕТКИ КЛАУЗ")
    logger.info("=" * 50)
    
    success = True
    
    # Проверяем Ollama
    if not check_ollama():
        logger.error("Установите Ollama: https://ollama.ai/")
        return False
    
    # Тестируем модель
    if not test_model():
        logger.error("Проблемы с моделью. Попробуйте: ollama pull llama3:8b-instruct")
        return False
    
    # Тестируем разметку
    if not test_clause_labeling():
        success = False
    
    if success:
        logger.info("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        logger.info("Система готова к работе. Запустите:")
        logger.info("python scripts/labeling/label_clauses_ollama.py")
    else:
        logger.error("\n❌ ЕСТЬ ПРОБЛЕМЫ В ТЕСТАХ")
    
    return success

if __name__ == "__main__":
    main()
