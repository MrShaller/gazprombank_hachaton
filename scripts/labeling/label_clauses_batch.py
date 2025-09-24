#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Пакетная обработка клауз с возможностью возобновления

Этот скрипт позволяет обрабатывать клаузы порциями с сохранением промежуточных результатов
и возможностью возобновления работы с того места, где остановились.
"""

import pandas as pd
import json
import os
import argparse
from pathlib import Path
from label_clauses_ollama import OllamaClauseLabeler, create_summary_stats
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BatchClauseProcessor:
    def __init__(self, input_file: str, output_dir: str, model_name: str = "llama3.1:8b-instruct-q8_0"):
        """
        Инициализация пакетного процессора
        
        Args:
            input_file: Путь к исходному CSV файлу
            output_dir: Директория для сохранения результатов
            model_name: Название модели Ollama
        """
        self.input_file = input_file
        self.output_dir = Path(output_dir)
        self.model_name = model_name
        
        # Создаем директории
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.batches_dir = self.output_dir / "batches"
        self.batches_dir.mkdir(exist_ok=True)
        
        # Инициализируем классификатор
        self.labeler = OllamaClauseLabeler(model_name)
        
        # Файлы для отслеживания прогресса
        self.progress_file = self.output_dir / "progress.json"
        self.final_output = self.output_dir / "clauses_labeled.json"
        self.stats_output = self.output_dir / "clauses_labeled_stats.json"
    
    def load_progress(self) -> dict:
        """Загрузка информации о прогрессе"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"processed_batches": [], "last_batch_idx": -1, "total_processed": 0}
    
    def save_progress(self, progress: dict):
        """Сохранение информации о прогрессе"""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    
    def process_batch(self, clauses_df: pd.DataFrame, batch_idx: int, 
                     start_idx: int, batch_size: int) -> str:
        """
        Обработка одного батча
        
        Args:
            clauses_df: DataFrame с клаузами
            batch_idx: Номер батча
            start_idx: Начальный индекс
            batch_size: Размер батча
            
        Returns:
            Путь к файлу с результатами батча
        """
        batch_file = self.batches_dir / f"batch_{batch_idx:04d}.json"
        
        # Если батч уже обработан, пропускаем
        if batch_file.exists():
            logger.info(f"Батч {batch_idx} уже обработан, пропускаем")
            return str(batch_file)
        
        logger.info(f"Обрабатываем батч {batch_idx} (индексы {start_idx}-{start_idx + batch_size - 1})")
        
        # Обрабатываем батч
        results = self.labeler.process_clauses_batch(clauses_df, start_idx, batch_size)
        
        # Сохраняем результаты батча
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Батч {batch_idx} сохранен в {batch_file}")
        return str(batch_file)
    
    def merge_batches(self, batch_files: list) -> list:
        """
        Объединение результатов всех батчей
        
        Args:
            batch_files: Список путей к файлам батчей
            
        Returns:
            Объединенный список результатов
        """
        logger.info("Объединяем результаты всех батчей...")
        
        all_results = []
        for batch_file in batch_files:
            if os.path.exists(batch_file):
                with open(batch_file, 'r', encoding='utf-8') as f:
                    batch_results = json.load(f)
                    all_results.extend(batch_results)
        
        logger.info(f"Объединено {len(all_results)} результатов")
        return all_results
    
    def process_all_clauses(self, batch_size: int = 100, max_clauses: int = None):
        """
        Обработка всех клауз с разбивкой на батчи
        
        Args:
            batch_size: Размер одного батча
            max_clauses: Максимальное количество клауз для обработки (None = все)
        """
        start_time = time.time()
        
        # Загружаем данные
        logger.info(f"Загружаем данные из {self.input_file}")
        clauses_df = pd.read_csv(self.input_file)
        
        if max_clauses:
            clauses_df = clauses_df.head(max_clauses)
            logger.info(f"Ограничиваем обработку до {max_clauses} клауз")
        
        total_clauses = len(clauses_df)
        total_batches = (total_clauses + batch_size - 1) // batch_size
        
        logger.info(f"Всего клауз: {total_clauses}")
        logger.info(f"Размер батча: {batch_size}")
        logger.info(f"Всего батчей: {total_batches}")
        
        # Загружаем прогресс
        progress = self.load_progress()
        start_batch = progress["last_batch_idx"] + 1
        
        if start_batch > 0:
            logger.info(f"Возобновляем работу с батча {start_batch}")
        
        batch_files = []
        
        try:
            # Обрабатываем батчи
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                current_batch_size = min(batch_size, total_clauses - start_idx)
                
                if batch_idx < start_batch:
                    # Батч уже обработан, добавляем файл в список
                    batch_file = self.batches_dir / f"batch_{batch_idx:04d}.json"
                    if batch_file.exists():
                        batch_files.append(str(batch_file))
                    continue
                
                # Обрабатываем текущий батч
                batch_file = self.process_batch(clauses_df, batch_idx, start_idx, current_batch_size)
                batch_files.append(batch_file)
                
                # Обновляем прогресс
                progress["processed_batches"].append(batch_idx)
                progress["last_batch_idx"] = batch_idx
                progress["total_processed"] += current_batch_size
                self.save_progress(progress)
                
                logger.info(f"Прогресс: {progress['total_processed']}/{total_clauses} клауз ({progress['total_processed']/total_clauses*100:.1f}%)")
        
        except KeyboardInterrupt:
            logger.info("Обработка прервана пользователем. Прогресс сохранен.")
            return
        except Exception as e:
            logger.error(f"Ошибка при обработке: {e}")
            return
        
        # Объединяем все результаты
        all_results = self.merge_batches(batch_files)
        
        # Сохраняем итоговый файл
        with open(self.final_output, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        # Создаем статистику
        stats = create_summary_stats(all_results)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        stats["execution_time_seconds"] = total_time
        stats["execution_time_minutes"] = total_time / 60
        stats["avg_time_per_clause"] = total_time / len(all_results) if all_results else 0
        stats["batch_size"] = batch_size
        stats["total_batches"] = total_batches
        
        # Сохраняем статистику в reports/labeling
        project_root = Path(__file__).parent.parent.parent
        stats_output = project_root / "reports/labeling/batch_clauses_labeled_stats.json"
        os.makedirs(stats_output.parent, exist_ok=True)
        
        with open(stats_output, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        # Выводим итоговую статистику
        logger.info("=" * 60)
        logger.info("ОБРАБОТКА ЗАВЕРШЕНА")
        logger.info("=" * 60)
        logger.info(f"Обработано клауз: {len(all_results)}")
        logger.info(f"Общее время: {total_time/60:.1f} минут")
        logger.info(f"Среднее время на клаузу: {total_time/len(all_results):.2f} секунд")
        logger.info(f"Результаты: {self.final_output}")
        logger.info(f"Статистика: {stats_output}")
        logger.info(f"📁 Структура проекта:")
        logger.info(f"   - Данные: {project_root}/data/processed/labeling/")
        logger.info(f"   - Отчеты: {project_root}/reports/labeling/")
        
        # Очищаем файл прогресса
        if self.progress_file.exists():
            self.progress_file.unlink()
            logger.info("Файл прогресса очищен")

def main():
    parser = argparse.ArgumentParser(description='Пакетная разметка клауз с помощью Ollama')
    # Определяем корневую папку проекта
    project_root = Path(__file__).parent.parent.parent
    
    parser.add_argument('--input', 
                       default=str(project_root / 'data/interim/clauses.csv'),
                       help='Путь к входному CSV файлу')
    parser.add_argument('--output-dir',
                       default=str(project_root / 'data/processed/labeling'),
                       help='Директория для сохранения результатов')
    parser.add_argument('--batch-size', type=int, default=50,
                       help='Размер батча для обработки')
    parser.add_argument('--max-clauses', type=int, default=1000,
                       help='Максимальное количество клауз для обработки (None = все)')
    parser.add_argument('--model', default='llama3.1:8b-instruct-q8_0',
                       help='Название модели Ollama')
    
    args = parser.parse_args()
    
    # Создаем процессор
    processor = BatchClauseProcessor(args.input, args.output_dir, args.model)
    
    # Загружаем полные тексты отзывов
    merged_json_path = project_root / "data/raw/merged.json"
    if merged_json_path.exists():
        processor.labeler.load_review_texts(str(merged_json_path))
    else:
        logger.warning("Файл merged.json не найден, обработка без полного контекста")
    
    # Запускаем обработку
    processor.process_all_clauses(args.batch_size, args.max_clauses)

if __name__ == "__main__":
    main()
