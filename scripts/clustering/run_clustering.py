#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт-лаунчер для запуска всех методов кластеризации

Этот скрипт последовательно выполняет все методы кластеризации
и создает итоговый отчет с рекомендациями.
"""

import os
import sys
import argparse
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

def main():
    parser = argparse.ArgumentParser(description='Запуск тематической кластеризации отзывов')
    parser.add_argument('--data-path', 
                       default=str(project_root / 'data/raw/merged (1).json'),
                       help='Путь к файлу с данными')
    parser.add_argument('--methods', 
                       nargs='+',
                       choices=['embedding', 'topic', 'tfidf', 'all'],
                       default=['all'],
                       help='Методы для запуска')
    parser.add_argument('--quick', 
                       action='store_true',
                       help='Быстрый режим (ограниченная выборка)')
    parser.add_argument('--no-viz', 
                       action='store_true',
                       help='Отключить создание визуализаций')
    
    args = parser.parse_args()
    
    print("🚀 Запуск тематической кластеризации отзывов банка")
    print("=" * 60)
    print(f"📁 Данные: {args.data_path}")
    print(f"🔧 Методы: {args.methods}")
    print(f"⚡ Быстрый режим: {'Да' if args.quick else 'Нет'}")
    print(f"📊 Визуализации: {'Нет' if args.no_viz else 'Да'}")
    print()
    
    # Создаем необходимые папки
    os.makedirs(project_root / 'data/processed/clustering', exist_ok=True)
    os.makedirs(project_root / 'reports/clustering', exist_ok=True)
    
    methods_to_run = args.methods if 'all' not in args.methods else ['embedding', 'topic', 'tfidf']
    
    # Запускаем выбранные методы
    if 'embedding' in methods_to_run:
        print("🧠 Запуск кластеризации на основе эмбеддингов...")
        run_embedding_clustering(args.data_path, args.quick, args.no_viz)
    
    if 'topic' in methods_to_run:
        print("📝 Запуск тематического моделирования...")
        run_topic_modeling(args.data_path, args.quick, args.no_viz)
    
    if 'tfidf' in methods_to_run:
        print("📊 Запуск TF-IDF кластеризации...")
        run_tfidf_clustering(args.data_path, args.quick, args.no_viz)
    
    # Запускаем оценку результатов
    if len(methods_to_run) > 1:
        print("📈 Запуск комплексной оценки результатов...")
        run_evaluation(args.data_path)
    
    print("\n✅ Кластеризация завершена!")
    print("📂 Результаты сохранены в:")
    print(f"   - Данные: {project_root}/data/processed/clustering/")
    print(f"   - Отчеты: {project_root}/reports/clustering/")

def run_embedding_clustering(data_path, quick=False, no_viz=False):
    """Запуск кластеризации на основе эмбеддингов"""
    try:
        from embedding_clustering import EmbeddingClustering
        
        clustering = EmbeddingClustering(data_path)
        
        # Загружаем данные с ограничением для избежания проблем с памятью
        max_samples = 1000 if quick else 10000
        clustering.load_data(max_samples=max_samples)
        
        if quick:
            print("  ⚡ Быстрый режим: используем до 1000 отзывов")
        else:
            print("  📊 Обычный режим: используем до 10000 отзывов")
        
        clustering.load_model('cointegrated/rubert-tiny2')  # Быстрая модель
        clustering.create_embeddings(batch_size=16)  # Уменьшаем размер батча
        clustering.perform_clustering()
        clustering.analyze_clusters()
        
        if not no_viz:
            clustering.visualize_clusters()
        
        output_path = str(project_root / 'data/processed/clustering/embedding_clustering_results.json')
        clustering.save_results(output_path)
        
        print("  ✅ Кластеризация на основе эмбеддингов завершена")
        
    except Exception as e:
        print(f"  ❌ Ошибка в кластеризации на основе эмбеддингов: {str(e)}")
        import traceback
        print(f"  Подробности: {traceback.format_exc()}")

def run_topic_modeling(data_path, quick=False, no_viz=False):
    """Запуск тематического моделирования"""
    try:
        from topic_modeling import TopicModeling
        
        topic_modeling = TopicModeling(data_path)
        
        # Загружаем данные с ограничением для избежания проблем с памятью
        max_samples = 1000 if quick else 40000
        topic_modeling.load_data(max_samples=max_samples)
        
        if quick:
            print("  ⚡ Быстрый режим: используем до 1000 отзывов")
        else:
            print("  📊 Обычный режим: используем до 10000 отзывов")
        
        topic_modeling.prepare_texts()
        
        # LDA с ограниченным диапазоном в быстром режиме
        topics_range = (3, 10) if quick else (5, 20)
        lda_results = topic_modeling.lda_modeling(n_topics_range=topics_range)
        
        # BERTopic (пропускаем в быстром режиме из-за требований к ресурсам)
        if not quick:
            bertopic_results = topic_modeling.bertopic_modeling()
            topic_modeling.compare_methods(lda_results, bertopic_results)
        else:
            bertopic_results = None
            print("  ⚡ BERTopic пропущен в быстром режиме")
        
        output_path = str(project_root / 'data/processed/clustering/topic_modeling_results.json')
        if bertopic_results:
            topic_modeling.save_results(lda_results, bertopic_results, output_path)
        else:
            # Сохраняем только LDA результаты
            topic_modeling.df.to_json(output_path, orient='records', indent=2)
        
        print("  ✅ Тематическое моделирование завершено")
        
    except Exception as e:
        print(f"  ❌ Ошибка в тематическом моделировании: {e}")
        import traceback
        print(f"  Подробности: {traceback.format_exc()}")

def run_tfidf_clustering(data_path, quick=False, no_viz=False):
    """Запуск TF-IDF кластеризации"""
    try:
        from tfidf_clustering import TfIdfClustering
        
        clustering = TfIdfClustering(data_path)
        
        # Загружаем данные с ограничением для избежания проблем с памятью
        max_samples = 1000 if quick else 40000
        clustering.load_data(max_samples=max_samples)
        
        if quick:
            print("  ⚡ Быстрый режим: используем до 1000 отзывов")
        else:
            print("  📊 Обычный режим: используем до 10000 отзывов")
        
        clustering.prepare_texts()
        
        # Уменьшенные параметры для быстрого режима
        max_features = 1000 if quick else 5000
        clustering.create_tfidf_matrix(max_features=max_features)
        
        # Ограниченный набор алгоритмов в быстром режиме
        algorithms = ['kmeans'] if quick else ['kmeans', 'agglomerative', 'dbscan']
        results = clustering.perform_clustering(algorithms=algorithms)
        
        if not no_viz:
            if not quick:
                clustering.create_word_clouds(results)
            clustering.visualize_clusters(results)
            clustering.compare_algorithms(results)
        
        output_path = str(project_root / 'data/processed/clustering/tfidf_clustering_results.json')
        clustering.save_results(results, output_path)
        
        print("  ✅ TF-IDF кластеризация завершена")
        
    except Exception as e:
        print(f"  ❌ Ошибка в TF-IDF кластеризации: {e}")
        import traceback
        print(f"  Подробности: {traceback.format_exc()}")

def run_evaluation(data_path):
    """Запуск комплексной оценки"""
    try:
        from clustering_evaluation import ClusteringEvaluation
        
        results_paths = {
            'embedding_clustering': str(project_root / 'data/processed/clustering/embedding_clustering_results.json'),
            'topic_modeling': str(project_root / 'data/processed/clustering/topic_modeling_results.json'),
            'tfidf_clustering': str(project_root / 'data/processed/clustering/tfidf_clustering_results.json')
        }
        
        evaluation = ClusteringEvaluation(data_path)
        evaluation.load_original_data()
        evaluation.load_clustering_results(results_paths)
        
        # Анализы
        consistency_results = evaluation.analyze_cluster_consistency()
        alignment_results = evaluation.analyze_product_type_alignment()
        profiles = evaluation.create_cluster_profiles()
        quality_metrics = evaluation.evaluate_clustering_quality()
        
        evaluation.create_summary_visualization(quality_metrics)
        recommendations = evaluation.generate_recommendations(quality_metrics, alignment_results)
        
        # Сохранение отчета
        output_path = str(project_root / 'reports/clustering/clustering_evaluation_report.txt')
        evaluation.save_evaluation_report(
            quality_metrics, alignment_results, recommendations, output_path
        )
        
        print("  ✅ Комплексная оценка завершена")
        
    except Exception as e:
        print(f"  ❌ Ошибка в комплексной оценке: {e}")

if __name__ == "__main__":
    main()
