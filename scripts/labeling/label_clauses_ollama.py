#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Разметка текстовых клауз по банковским продуктам и тональности с помощью Ollama

Этот скрипт обрабатывает клаузы из CSV файла и использует LLM (Ollama) 
для определения банковских продуктов и их тональности.
"""

import pandas as pd
import json
import subprocess
import time
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OllamaClauseLabeler:
    def __init__(self, model_name: str = "gpt-oss:20b"):
        """
        Инициализация класса для разметки клауз
        
        Args:
            model_name: Название модели Ollama
        """
        self.model_name = model_name
        self.allowed_topics = [
            "Дебетовая карта", "Кредитная карта", "Дистанционное обслуживание", 
            "Другое", "Денежные переводы", "Потребительский кредит", "Ипотека", 
            "Автокредит", "Рефинансирование кредитов", "Вклады", 
            "Мобильное приложение", "Обслуживание", "Обмен валют"
        ]
        self.allowed_sentiments = ["положительно", "нейтрально", "отрицательно"]
        
        # Словарь для хранения полных текстов отзывов
        self.review_texts = {}
        
        # Проверяем доступность Ollama
        self._check_ollama_availability()
    
    def _check_ollama_availability(self):
        """Проверка доступности Ollama и модели"""
        try:
            # Проверяем, что Ollama установлена
            result = subprocess.run(['ollama', 'list'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                raise RuntimeError("Ollama не найдена или не запущена")
            
            # Проверяем наличие модели
            if self.model_name not in result.stdout:
                logger.warning(f"Модель {self.model_name} не найдена. Попытка загрузки...")
                self._pull_model()
            
            logger.info(f"Ollama и модель {self.model_name} готовы к работе")
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Timeout при проверке Ollama")
        except FileNotFoundError:
            raise RuntimeError("Ollama не установлена. Установите с https://ollama.ai/")
    
    def _pull_model(self):
        """Загрузка модели если она отсутствует"""
        try:
            logger.info(f"Загружаем модель {self.model_name}...")
            result = subprocess.run(['ollama', 'pull', self.model_name], 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                raise RuntimeError(f"Не удалось загрузить модель: {result.stderr}")
            logger.info("Модель успешно загружена")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Timeout при загрузке модели")
    
    def load_review_texts(self, merged_json_path: str):
        """
        Загрузка полных текстов отзывов из merged.json
        
        Args:
            merged_json_path: Путь к файлу merged.json
        """
        logger.info(f"Загружаем полные тексты отзывов из {merged_json_path}")
        
        try:
            with open(merged_json_path, 'r', encoding='utf-8') as f:
                reviews_data = json.load(f)
            
            for review in reviews_data:
                review_id = review['review_id']
                review_text = review['review_text']
                self.review_texts[review_id] = review_text
            
            logger.info(f"Загружено {len(self.review_texts)} полных текстов отзывов")
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке текстов отзывов: {e}")
            raise
    
    def create_prompt(self, clause: str, full_review_text: str = None) -> str:
        """
        Создание промпта для LLM
        
        Args:
            clause: Текст клаузы для анализа
            full_review_text: Полный текст отзыва для контекста
            
        Returns:
            Готовый промпт для отправки в LLM
        """
        context_section = ""
        if full_review_text:
            context_section = f"""
КОНТЕКСТ - полный текст отзыва:
"{full_review_text}"

"""

        prompt = f"""Ты классификатор банковских клауз. Твоя задача – выделять банковские продукты/услуги и их тональности в конкретной клаузе, используя контекст всего отзыва.

{context_section}Правила:
- Размечай только по списку категорий: {self.allowed_topics}.
- Тональности только из списка: {self.allowed_sentiments}.
- ВАЖНО: Количество продуктов и тональностей должно быть СТРОГО РАВНЫМ. На каждый найденный продукт/услугу должна быть соответствующая тональность.
- Если в клаузе нет ЯВНЫХ банковских продуктов, оставь оба списка пустыми.
- Если тональность неясна, используй "нейтрально".
- Анализируй именно данную клаузу, но учитывай контекст всего отзыва для понимания тональности.
- Отвечай только JSON без пояснений.

Примеры:
Вход: "Очень понравилось обслуживание в отделении, но мобильное приложение часто зависает."
Выход:
{{
  "topics": ["Обслуживание", "Мобильное приложение"],
  "sentiments": ["положительно", "отрицательно"]
}}

Вход: "Взял автокредит."
Выход:
{{
  "topics": ["Автокредит"],
  "sentiments": ["нейтрально"]
}}

Вход: "Пришел в банк утром."
Выход:
{{
  "topics": [],
  "sentiments": []
}}

Теперь размечай следующую клаузу:
"{clause}"
"""
        return prompt
    
    def call_ollama(self, prompt: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Вызов Ollama для обработки промпта
        
        Args:
            prompt: Промпт для LLM
            max_retries: Максимальное количество попыток
            
        Returns:
            Ответ LLM в виде словаря
        """
        for attempt in range(max_retries):
            try:
                # Вызываем Ollama через subprocess
                result = subprocess.run(
                    ['ollama', 'run', self.model_name],
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=60  # Таймаут 60 секунд
                )
                
                if result.returncode != 0:
                    logger.warning(f"Ollama вернула ошибку (попытка {attempt + 1}): {result.stderr}")
                    continue
                
                # Парсим JSON ответ
                response_text = result.stdout.strip()
                
                # Пытаемся извлечь JSON из ответа
                try:
                    # Ищем JSON в ответе (может быть обернут в другой текст)
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = response_text[start_idx:end_idx]
                        response_data = json.loads(json_str)
                        
                        # Валидация ответа
                        if self._validate_response(response_data):
                            return response_data
                        else:
                            logger.warning(f"Невалидный ответ (попытка {attempt + 1}): {response_data}")
                    else:
                        logger.warning(f"JSON не найден в ответе (попытка {attempt + 1}): {response_text}")
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Ошибка парсинга JSON (попытка {attempt + 1}): {e}")
                    logger.warning(f"Ответ: {response_text}")
                
            except subprocess.TimeoutExpired:
                logger.warning(f"Timeout при вызове Ollama (попытка {attempt + 1})")
            except Exception as e:
                logger.warning(f"Ошибка при вызове Ollama (попытка {attempt + 1}): {e}")
        
        # Если все попытки неудачны, возвращаем пустой результат
        logger.error("Все попытки вызова Ollama неудачны")
        return {"topics": [], "sentiments": []}
    
    def _validate_response(self, response: Dict[str, Any]) -> bool:
        """
        Валидация ответа от LLM
        
        Args:
            response: Ответ от LLM
            
        Returns:
            True если ответ валидный
        """
        if not isinstance(response, dict):
            return False
        
        if "topics" not in response or "sentiments" not in response:
            return False
        
        if not isinstance(response["topics"], list) or not isinstance(response["sentiments"], list):
            return False
        
        # ВАЖНО: Проверяем равенство количества продуктов и тональностей
        if len(response["topics"]) != len(response["sentiments"]):
            logger.warning(f"Количество продуктов ({len(response['topics'])}) не равно количеству тональностей ({len(response['sentiments'])})")
            return False
        
        # Проверяем, что все топики из разрешенного списка
        for topic in response["topics"]:
            if topic not in self.allowed_topics:
                logger.warning(f"Неразрешенный топик: {topic}")
                return False
        
        # Проверяем, что все тональности из разрешенного списка
        for sentiment in response["sentiments"]:
            if sentiment not in self.allowed_sentiments:
                logger.warning(f"Неразрешенная тональность: {sentiment}")
                return False
        
        return True
    
    def process_clause(self, clause_row: pd.Series) -> Dict[str, Any]:
        """
        Обработка одной клаузы
        
        Args:
            clause_row: Строка DataFrame с данными клаузы
            
        Returns:
            Результат разметки клаузы
        """
        clause_text = clause_row['clause']
        clause_id = clause_row['clause_id']
        review_id = clause_row['review_id']
        
        # Получаем полный текст отзыва для контекста
        full_review_text = self.review_texts.get(review_id, None)
        if full_review_text is None:
            logger.warning(f"Полный текст отзыва {review_id} не найден, используем только клаузу")
        
        # Создаем промпт с контекстом
        prompt = self.create_prompt(clause_text, full_review_text)
        
        # Вызываем LLM
        llm_response = self.call_ollama(prompt)
        
        # Формируем результат
        result = {
            "clause_id": clause_id,
            "review_id": review_id,
            "clause": clause_text,
            "topics": llm_response.get("topics", []),
            "sentiments": llm_response.get("sentiments", []),
            "has_full_context": full_review_text is not None
        }
        
        return result
    
    def process_clauses_batch(self, clauses_df: pd.DataFrame, 
                            start_idx: int = 0, batch_size: int = 1000) -> List[Dict[str, Any]]:
        """
        Обработка батча клауз
        
        Args:
            clauses_df: DataFrame с клаузами
            start_idx: Индекс начала обработки
            batch_size: Размер батча
            
        Returns:
            Список результатов разметки
        """
        end_idx = min(start_idx + batch_size, len(clauses_df))
        batch_df = clauses_df.iloc[start_idx:end_idx]
        
        results = []
        total_clauses = len(batch_df)
        
        logger.info(f"Начинаем обработку {total_clauses} клауз (индексы {start_idx}-{end_idx-1})")
        
        for idx, (_, row) in enumerate(batch_df.iterrows()):
            try:
                logger.info(f"Обрабатываем клаузу {idx + 1}/{total_clauses} (ID: {row['clause_id']})")
                
                result = self.process_clause(row)
                results.append(result)
                
                # Логируем результат
                logger.info(f"Результат: topics={result['topics']}, sentiments={result['sentiments']}")
                
                # Небольшая пауза между запросами
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Ошибка при обработке клаузы {row['clause_id']}: {e}")
                # Добавляем пустой результат в случае ошибки
                results.append({
                    "clause_id": row['clause_id'],
                    "review_id": row['review_id'],
                    "clause": row['clause'],
                    "topics": [],
                    "sentiments": []
                })
        
        return results

def load_clauses_data(file_path: str) -> pd.DataFrame:
    """
    Загрузка данных клауз из CSV файла
    
    Args:
        file_path: Путь к CSV файлу
        
    Returns:
        DataFrame с данными клауз
    """
    logger.info(f"Загружаем данные из {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Загружено {len(df)} клауз")
        logger.info(f"Колонки: {list(df.columns)}")
        return df
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {e}")
        raise

def save_results(results: List[Dict[str, Any]], output_path: str):
    """
    Сохранение результатов в JSON файл
    
    Args:
        results: Список результатов разметки
        output_path: Путь для сохранения
    """
    logger.info(f"Сохраняем {len(results)} результатов в {output_path}")
    
    # Создаем директорию если не существует
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Сохраняем результаты
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info("Результаты успешно сохранены")

def create_summary_stats(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Создание статистики по результатам разметки
    
    Args:
        results: Список результатов разметки
        
    Returns:
        Словарь со статистикой
    """
    total_clauses = len(results)
    
    # Статистика по топикам
    all_topics = []
    for result in results:
        all_topics.extend(result['topics'])
    topic_counts = pd.Series(all_topics).value_counts().to_dict()
    
    # Статистика по тональностям
    all_sentiments = []
    for result in results:
        all_sentiments.extend(result['sentiments'])
    sentiment_counts = pd.Series(all_sentiments).value_counts().to_dict()
    
    # Статистика по количеству топиков/тональностей на клаузу
    topics_per_clause = [len(result['topics']) for result in results]
    sentiments_per_clause = [len(result['sentiments']) for result in results]
    
    # Статистика по контексту
    clauses_with_context = sum(1 for result in results if result.get('has_full_context', False))
    
    # Проверяем равенство количества продуктов и тональностей
    equal_counts = sum(1 for result in results if len(result['topics']) == len(result['sentiments']))
    
    stats = {
        "total_clauses": total_clauses,
        "clauses_with_topics": sum(1 for result in results if result['topics']),
        "clauses_with_sentiments": sum(1 for result in results if result['sentiments']),
        "clauses_with_full_context": clauses_with_context,
        "clauses_with_equal_counts": equal_counts,
        "equal_counts_percentage": (equal_counts / total_clauses * 100) if total_clauses > 0 else 0,
        "topic_distribution": topic_counts,
        "sentiment_distribution": sentiment_counts,
        "avg_topics_per_clause": sum(topics_per_clause) / len(topics_per_clause) if topics_per_clause else 0,
        "avg_sentiments_per_clause": sum(sentiments_per_clause) / len(sentiments_per_clause) if sentiments_per_clause else 0
    }
    
    return stats

def main():
    """Основная функция"""
    # Пути к файлам
    project_root = Path(__file__).parent.parent.parent
    input_file = str(project_root / "data/interim/clauses.csv")
    output_file = str(project_root / "data/processed/labeling/clauses_labeled.json")
    
    # Параметры обработки
    TEST_SIZE = None  # Количество клауз для тестирования (легко изменить) None для всех
    
    try:
        # Засекаем время начала
        start_time = time.time()
        
        # Загружаем данные
        clauses_df = load_clauses_data(input_file)
        
        # Создаем экземпляр классификатора
        labeler = OllamaClauseLabeler()
        
        # Загружаем полные тексты отзывов для контекста
        merged_json_path = str(project_root / "data/raw/merged.json")
        labeler.load_review_texts(merged_json_path)
        
        # Обрабатываем клаузы (все если TEST_SIZE=None)
        batch_size = len(clauses_df) if TEST_SIZE is None else TEST_SIZE
        results = labeler.process_clauses_batch(clauses_df, start_idx=0, batch_size=batch_size)
        
        # Засекаем время окончания
        end_time = time.time()
        total_time = end_time - start_time
        
        # Создаем статистику
        stats = create_summary_stats(results)
        
        # Добавляем информацию о времени выполнения
        stats["execution_time_seconds"] = total_time
        stats["execution_time_minutes"] = total_time / 60
        stats["avg_time_per_clause"] = total_time / len(results) if results else 0
        
        # Сохраняем результаты
        save_results(results, output_file)
        
        # Сохраняем статистику в reports/labeling
        stats_file = str(project_root / "reports/labeling/clauses_labeled_stats.json")
        os.makedirs(os.path.dirname(stats_file), exist_ok=True)
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        # Выводим итоговую статистику
        logger.info("=" * 60)
        logger.info("ИТОГОВАЯ СТАТИСТИКА")
        logger.info("=" * 60)
        logger.info(f"Обработано клауз: {stats['total_clauses']}")
        logger.info(f"Клауз с полным контекстом: {stats['clauses_with_full_context']} ({stats['clauses_with_full_context']/stats['total_clauses']*100:.1f}%)")
        logger.info(f"Клауз с топиками: {stats['clauses_with_topics']} ({stats['clauses_with_topics']/stats['total_clauses']*100:.1f}%)")
        logger.info(f"Клауз с тональностями: {stats['clauses_with_sentiments']} ({stats['clauses_with_sentiments']/stats['total_clauses']*100:.1f}%)")
        logger.info(f"Клауз с равным количеством продуктов/тональностей: {stats['clauses_with_equal_counts']} ({stats['equal_counts_percentage']:.1f}%)")
        logger.info(f"Среднее топиков на клаузу: {stats['avg_topics_per_clause']:.2f}")
        logger.info(f"Среднее тональностей на клаузу: {stats['avg_sentiments_per_clause']:.2f}")
        logger.info(f"Общее время выполнения: {stats['execution_time_minutes']:.1f} минут")
        logger.info(f"Среднее время на клаузу: {stats['avg_time_per_clause']:.2f} секунд")
        
        logger.info("\nТоп-5 наиболее частых топиков:")
        for topic, count in list(stats['topic_distribution'].items())[:5]:
            logger.info(f"  {topic}: {count}")
        
        logger.info("\nРаспределение тональностей:")
        for sentiment, count in stats['sentiment_distribution'].items():
            logger.info(f"  {sentiment}: {count}")
        
        logger.info(f"\n✅ Результаты сохранены в: {output_file}")
        logger.info(f"📊 Статистика сохранена в: {stats_file}")
        logger.info(f"📁 Структура проекта:")
        logger.info(f"   - Данные: {project_root}/data/processed/labeling/")
        logger.info(f"   - Отчеты: {project_root}/reports/labeling/")
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    main()
