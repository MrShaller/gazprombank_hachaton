#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Оценка и сравнение результатов различных методов кластеризации

Этот скрипт сравнивает результаты всех методов кластеризации
и создает итоговый отчет с рекомендациями.
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')

# Для метрик
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

class ClusteringEvaluation:
    def __init__(self, data_path):
        """
        Инициализация класса для оценки кластеризации
        
        Args:
            data_path (str): Путь к исходным данным
        """
        self.data_path = data_path
        self.original_data = None
        self.results_data = {}
        self.evaluation_metrics = {}
        
    def load_original_data(self):
        """Загрузка исходных данных"""
        print("Загружаем исходные данные...")
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.original_data = pd.DataFrame(json.load(f))
        print(f"Загружено {len(self.original_data)} отзывов")
    
    def load_clustering_results(self, results_paths):
        """
        Загрузка результатов кластеризации
        
        Args:
            results_paths (dict): Словарь с путями к результатам разных методов
        """
        print("Загружаем результаты кластеризации...")
        
        for method_name, path in results_paths.items():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.results_data[method_name] = pd.DataFrame(data)
                print(f"  {method_name}: {len(data)} записей")
            except FileNotFoundError:
                print(f"  Предупреждение: файл {path} не найден")
                continue
    
    def analyze_cluster_consistency(self):
        """Анализ согласованности кластеров между методами"""
        print("\nАнализ согласованности кластеров между методами:")
        print("=" * 50)
        
        # Получаем все доступные методы кластеризации
        clustering_columns = []
        common_df = None
        
        for method_name, df in self.results_data.items():
            # Находим колонки с результатами кластеризации
            cluster_cols = [col for col in df.columns if 'cluster' in col.lower() or 'topic' in col.lower()]
            
            if cluster_cols:
                if common_df is None:
                    common_df = df[['review_id'] + cluster_cols].copy()
                    for col in cluster_cols:
                        new_col = f"{method_name}_{col}"
                        common_df[new_col] = common_df[col]
                        clustering_columns.append(new_col)
                else:
                    # Объединяем по review_id
                    temp_df = df[['review_id'] + cluster_cols].copy()
                    for col in cluster_cols:
                        new_col = f"{method_name}_{col}"
                        temp_df[new_col] = temp_df[col]
                    common_df = common_df.merge(temp_df[['review_id', new_col]], on='review_id', how='inner')
                    clustering_columns.append(new_col)
        
        if common_df is None or len(clustering_columns) < 2:
            print("Недостаточно данных для сравнения методов")
            return None
        
        # Вычисляем метрики согласованности
        consistency_matrix = np.zeros((len(clustering_columns), len(clustering_columns)))
        
        for i, method1 in enumerate(clustering_columns):
            for j, method2 in enumerate(clustering_columns):
                if i != j:
                    # Убираем записи с отсутствующими значениями
                    mask = (common_df[method1].notna()) & (common_df[method2].notna())
                    if mask.sum() > 0:
                        labels1 = common_df.loc[mask, method1]
                        labels2 = common_df.loc[mask, method2]
                        
                        # Adjusted Rand Index
                        ari = adjusted_rand_score(labels1, labels2)
                        consistency_matrix[i, j] = ari
                else:
                    consistency_matrix[i, j] = 1.0
        
        # Визуализация матрицы согласованности
        plt.figure(figsize=(10, 8))
        sns.heatmap(consistency_matrix, 
                   annot=True, 
                   fmt='.3f',
                   xticklabels=[col.replace('_', '\n') for col in clustering_columns],
                   yticklabels=[col.replace('_', '\n') for col in clustering_columns],
                   cmap='viridis',
                   vmin=0, vmax=1)
        plt.title('Согласованность методов кластеризации\n(Adjusted Rand Index)')
        plt.tight_layout()
        plt.savefig('/Users/mishantique/Desktop/Projects/gazprombank_hachaton/reports/clustering/clustering_consistency_matrix.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
        
        # Выводим среднюю согласованность для каждого метода
        print("\nСредняя согласованность методов с другими:")
        for i, method in enumerate(clustering_columns):
            avg_consistency = np.mean([consistency_matrix[i, j] for j in range(len(clustering_columns)) if i != j])
            print(f"  {method}: {avg_consistency:.3f}")
        
        return consistency_matrix, clustering_columns
    
    def analyze_product_type_alignment(self):
        """Анализ соответствия кластеров реальным типам продуктов"""
        print("\nАнализ соответствия кластеров типам продуктов:")
        print("=" * 50)
        
        alignment_results = {}
        
        for method_name, df in self.results_data.items():
            print(f"\n{method_name.upper()}:")
            
            # Находим колонки с кластерами
            cluster_cols = [col for col in df.columns if 'cluster' in col.lower() or 'topic' in col.lower()]
            
            for cluster_col in cluster_cols:
                if cluster_col in df.columns and 'product_type' in df.columns:
                    # Создаем таблицу сопряженности
                    contingency_table = pd.crosstab(df[cluster_col], df['product_type'])
                    
                    # Вычисляем чистоту кластеров
                    cluster_purities = []
                    for cluster_id in contingency_table.index:
                        if cluster_id != -1:  # Исключаем outliers
                            cluster_row = contingency_table.loc[cluster_id]
                            purity = cluster_row.max() / cluster_row.sum()
                            cluster_purities.append(purity)
                            
                            # Находим доминирующий тип продукта
                            dominant_product = cluster_row.idxmax()
                            print(f"  Кластер {cluster_id}: {purity:.3f} чистоты, доминирует '{dominant_product}'")
                    
                    avg_purity = np.mean(cluster_purities) if cluster_purities else 0
                    alignment_results[f"{method_name}_{cluster_col}"] = {
                        'avg_purity': avg_purity,
                        'contingency_table': contingency_table,
                        'cluster_purities': cluster_purities
                    }
                    
                    print(f"  Средняя чистота кластеров: {avg_purity:.3f}")
        
        return alignment_results
    
    def create_cluster_profiles(self):
        """Создание профилей кластеров для каждого метода"""
        print("\nСоздаем профили кластеров...")
        
        profiles = {}
        
        for method_name, df in self.results_data.items():
            print(f"\nПрофили кластеров - {method_name.upper()}:")
            print("-" * 30)
            
            method_profiles = {}
            cluster_cols = [col for col in df.columns if 'cluster' in col.lower() or 'topic' in col.lower()]
            
            for cluster_col in cluster_cols[:1]:  # Берем первую колонку с кластерами
                if cluster_col not in df.columns:
                    continue
                    
                unique_clusters = sorted(df[cluster_col].unique())
                
                for cluster_id in unique_clusters:
                    if cluster_id == -1:
                        continue
                        
                    cluster_data = df[df[cluster_col] == cluster_id]
                    
                    # Профиль кластера
                    profile = {
                        'size': len(cluster_data),
                        'percentage': len(cluster_data) / len(df) * 100,
                        'top_products': cluster_data['product_type'].value_counts().head(3).to_dict(),
                        'avg_text_length': cluster_data['review_text'].str.len().mean(),
                        'date_range': {
                            'min': cluster_data['review_date'].min(),
                            'max': cluster_data['review_date'].max()
                        } if 'review_date' in cluster_data.columns else None
                    }
                    
                    method_profiles[cluster_id] = profile
                    
                    print(f"Кластер {cluster_id}:")
                    print(f"  Размер: {profile['size']} ({profile['percentage']:.1f}%)")
                    print(f"  Топ продукты: {profile['top_products']}")
                    print(f"  Средняя длина текста: {profile['avg_text_length']:.0f} символов")
            
            profiles[method_name] = method_profiles
        
        return profiles
    
    def evaluate_clustering_quality(self):
        """Оценка качества кластеризации различных методов"""
        print("\nОценка качества кластеризации:")
        print("=" * 50)
        
        quality_metrics = {}
        
        for method_name, df in self.results_data.items():
            print(f"\n{method_name.upper()}:")
            
            method_metrics = {}
            cluster_cols = [col for col in df.columns if 'cluster' in col.lower() or 'topic' in col.lower()]
            
            for cluster_col in cluster_cols:
                if cluster_col not in df.columns:
                    continue
                
                clusters = df[cluster_col].values
                unique_clusters = set(clusters)
                
                # Базовые метрики
                n_clusters = len(unique_clusters) - (1 if -1 in unique_clusters else 0)
                n_outliers = sum(1 for c in clusters if c == -1)
                
                # Распределение размеров кластеров
                cluster_sizes = [sum(1 for c in clusters if c == cluster_id) 
                               for cluster_id in unique_clusters if cluster_id != -1]
                
                if cluster_sizes:
                    size_std = np.std(cluster_sizes)
                    size_cv = size_std / np.mean(cluster_sizes) if np.mean(cluster_sizes) > 0 else 0
                else:
                    size_std = size_cv = 0
                
                # Соответствие типам продуктов (чистота)
                if 'product_type' in df.columns:
                    cluster_purities = []
                    for cluster_id in unique_clusters:
                        if cluster_id != -1:
                            cluster_mask = clusters == cluster_id
                            if cluster_mask.sum() > 0:
                                cluster_products = df.loc[cluster_mask, 'product_type']
                                purity = cluster_products.value_counts().max() / len(cluster_products)
                                cluster_purities.append(purity)
                    
                    avg_purity = np.mean(cluster_purities) if cluster_purities else 0
                else:
                    avg_purity = 0
                
                method_metrics[cluster_col] = {
                    'n_clusters': n_clusters,
                    'n_outliers': n_outliers,
                    'outlier_percentage': n_outliers / len(clusters) * 100,
                    'avg_cluster_size': np.mean(cluster_sizes) if cluster_sizes else 0,
                    'cluster_size_std': size_std,
                    'cluster_size_cv': size_cv,
                    'avg_purity': avg_purity
                }
                
                print(f"  {cluster_col}:")
                print(f"    Количество кластеров: {n_clusters}")
                print(f"    Outliers: {n_outliers} ({n_outliers / len(clusters) * 100:.1f}%)")
                print(f"    Средний размер кластера: {np.mean(cluster_sizes):.1f}")
                print(f"    Коэффициент вариации размеров: {size_cv:.3f}")
                print(f"    Средняя чистота: {avg_purity:.3f}")
            
            quality_metrics[method_name] = method_metrics
        
        return quality_metrics
    
    def create_summary_visualization(self, quality_metrics):
        """Создание сводной визуализации качества методов"""
        print("\nСоздаем сводную визуализацию...")
        
        # Собираем данные для сравнения
        methods = []
        n_clusters_list = []
        avg_purity_list = []
        outlier_percentage_list = []
        size_cv_list = []
        
        for method_name, method_data in quality_metrics.items():
            for cluster_col, metrics in method_data.items():
                methods.append(f"{method_name}\n{cluster_col}")
                n_clusters_list.append(metrics['n_clusters'])
                avg_purity_list.append(metrics['avg_purity'])
                outlier_percentage_list.append(metrics['outlier_percentage'])
                size_cv_list.append(metrics['cluster_size_cv'])
        
        # Создаем сравнительные графики
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Количество кластеров
        bars1 = ax1.bar(range(len(methods)), n_clusters_list)
        ax1.set_title('Количество кластеров')
        ax1.set_ylabel('Количество')
        ax1.set_xticks(range(len(methods)))
        ax1.set_xticklabels(methods, rotation=45, ha='right')
        
        # Средняя чистота
        bars2 = ax2.bar(range(len(methods)), avg_purity_list, color='green', alpha=0.7)
        ax2.set_title('Средняя чистота кластеров')
        ax2.set_ylabel('Чистота')
        ax2.set_ylim(0, 1)
        ax2.set_xticks(range(len(methods)))
        ax2.set_xticklabels(methods, rotation=45, ha='right')
        
        # Процент outliers
        bars3 = ax3.bar(range(len(methods)), outlier_percentage_list, color='red', alpha=0.7)
        ax3.set_title('Процент outliers')
        ax3.set_ylabel('Процент (%)')
        ax3.set_xticks(range(len(methods)))
        ax3.set_xticklabels(methods, rotation=45, ha='right')
        
        # Коэффициент вариации размеров кластеров
        bars4 = ax4.bar(range(len(methods)), size_cv_list, color='orange', alpha=0.7)
        ax4.set_title('Коэффициент вариации размеров кластеров')
        ax4.set_ylabel('Коэффициент вариации')
        ax4.set_xticks(range(len(methods)))
        ax4.set_xticklabels(methods, rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig('/Users/mishantique/Desktop/Projects/gazprombank_hachaton/reports/clustering/clustering_quality_comparison.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_recommendations(self, quality_metrics, alignment_results):
        """Генерация рекомендаций по выбору метода кластеризации"""
        print("\nРекомендации по выбору метода кластеризации:")
        print("=" * 50)
        
        # Оцениваем методы по различным критериям
        method_scores = {}
        
        for method_name, method_data in quality_metrics.items():
            for cluster_col, metrics in method_data.items():
                method_key = f"{method_name}_{cluster_col}"
                
                # Критерии оценки (нормализованные от 0 до 1)
                purity_score = metrics['avg_purity']  # Уже от 0 до 1
                
                # Оптимальное количество кластеров (предполагаем 10-20 как оптимум)
                n_clusters = metrics['n_clusters']
                if 8 <= n_clusters <= 25:
                    cluster_count_score = 1.0
                elif 5 <= n_clusters < 8 or 25 < n_clusters <= 30:
                    cluster_count_score = 0.7
                else:
                    cluster_count_score = 0.3
                
                # Процент outliers (меньше = лучше)
                outlier_score = max(0, 1 - metrics['outlier_percentage'] / 50)  # 50% outliers = 0 score
                
                # Сбалансированность кластеров (меньше CV = лучше)
                balance_score = max(0, 1 - metrics['cluster_size_cv'])
                
                # Общий счет
                total_score = (purity_score * 0.4 + 
                             cluster_count_score * 0.25 + 
                             outlier_score * 0.2 + 
                             balance_score * 0.15)
                
                method_scores[method_key] = {
                    'total_score': total_score,
                    'purity_score': purity_score,
                    'cluster_count_score': cluster_count_score,
                    'outlier_score': outlier_score,
                    'balance_score': balance_score,
                    'metrics': metrics
                }
        
        # Сортируем методы по общему счету
        sorted_methods = sorted(method_scores.items(), key=lambda x: x[1]['total_score'], reverse=True)
        
        print("Рейтинг методов (от лучшего к худшему):")
        for i, (method_key, scores) in enumerate(sorted_methods):
            print(f"\n{i+1}. {method_key}:")
            print(f"   Общий счет: {scores['total_score']:.3f}")
            print(f"   Чистота: {scores['purity_score']:.3f}")
            print(f"   Количество кластеров: {scores['metrics']['n_clusters']}")
            print(f"   Процент outliers: {scores['metrics']['outlier_percentage']:.1f}%")
        
        # Рекомендации по использованию
        print(f"\n🏆 РЕКОМЕНДУЕМЫЙ МЕТОД: {sorted_methods[0][0]}")
        best_method = sorted_methods[0]
        
        print("\nРекомендации по применению:")
        
        if best_method[1]['purity_score'] > 0.7:
            print("✅ Высокая чистота кластеров - метод хорошо разделяет типы продуктов")
        elif best_method[1]['purity_score'] > 0.5:
            print("⚠️  Средняя чистота кластеров - возможны смешанные кластеры")
        else:
            print("❌ Низкая чистота кластеров - кластеры плохо соответствуют типам продуктов")
        
        if best_method[1]['metrics']['outlier_percentage'] < 10:
            print("✅ Низкий процент outliers - большинство отзывов успешно кластеризованы")
        elif best_method[1]['metrics']['outlier_percentage'] < 25:
            print("⚠️  Умеренный процент outliers - часть отзывов требует дополнительного анализа")
        else:
            print("❌ Высокий процент outliers - многие отзывы не попали в основные кластеры")
        
        optimal_clusters = best_method[1]['metrics']['n_clusters']
        if 10 <= optimal_clusters <= 20:
            print("✅ Оптимальное количество кластеров для интерпретации")
        elif optimal_clusters < 10:
            print("⚠️  Малое количество кластеров - возможна чрезмерная генерализация")
        else:
            print("⚠️  Большое количество кластеров - может быть сложно интерпретировать")
        
        return sorted_methods
    
    def save_evaluation_report(self, quality_metrics, alignment_results, recommendations, output_path):
        """Сохранение итогового отчета по оценке"""
        print(f"\nСохраняем итоговый отчет в {output_path}...")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("ИТОГОВЫЙ ОТЧЕТ ПО ОЦЕНКЕ МЕТОДОВ КЛАСТЕРИЗАЦИИ\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("ЦЕЛЬ ИССЛЕДОВАНИЯ:\n")
            f.write("Тематическая кластеризация отзывов клиентов банка для выявления\n")
            f.write("основных групп обсуждаемых продуктов и услуг.\n\n")
            
            f.write("ИСПОЛЬЗОВАННЫЕ МЕТОДЫ:\n")
            f.write("1. Кластеризация на основе эмбеддингов (BERT/sentence-transformers)\n")
            f.write("2. Тематическое моделирование (LDA/BERTopic)\n")
            f.write("3. Кластеризация на основе TF-IDF (K-means, Agglomerative, DBSCAN)\n\n")
            
            f.write("РЕЗУЛЬТАТЫ ОЦЕНКИ:\n")
            f.write("-" * 30 + "\n\n")
            
            # Детальные метрики качества
            for method_name, method_data in quality_metrics.items():
                f.write(f"{method_name.upper()}:\n")
                for cluster_col, metrics in method_data.items():
                    f.write(f"  {cluster_col}:\n")
                    f.write(f"    Количество кластеров: {metrics['n_clusters']}\n")
                    f.write(f"    Outliers: {metrics['n_outliers']} ({metrics['outlier_percentage']:.1f}%)\n")
                    f.write(f"    Средний размер кластера: {metrics['avg_cluster_size']:.1f}\n")
                    f.write(f"    Коэффициент вариации размеров: {metrics['cluster_size_cv']:.3f}\n")
                    f.write(f"    Средняя чистота: {metrics['avg_purity']:.3f}\n")
                f.write("\n")
            
            f.write("РЕЙТИНГ МЕТОДОВ:\n")
            f.write("-" * 20 + "\n")
            for i, (method_key, scores) in enumerate(recommendations):
                f.write(f"{i+1}. {method_key} (общий счет: {scores['total_score']:.3f})\n")
                f.write(f"   - Чистота кластеров: {scores['purity_score']:.3f}\n")
                f.write(f"   - Количество кластеров: {scores['metrics']['n_clusters']}\n")
                f.write(f"   - Процент outliers: {scores['metrics']['outlier_percentage']:.1f}%\n\n")
            
            f.write(f"РЕКОМЕНДУЕМЫЙ МЕТОД: {recommendations[0][0]}\n\n")
            
            f.write("ВЫВОДЫ И РЕКОМЕНДАЦИИ:\n")
            f.write("-" * 30 + "\n")
            f.write("1. Для практического применения рекомендуется использовать метод с наивысшим рейтингом.\n")
            f.write("2. При выборе метода учитывайте баланс между чистотой кластеров и количеством outliers.\n")
            f.write("3. Для интерпретации результатов оптимально использовать 10-20 кластеров.\n")
            f.write("4. Рекомендуется дополнительно проанализировать outliers для выявления новых паттернов.\n\n")
            
            f.write("ПРИМЕНЕНИЕ РЕЗУЛЬТАТОВ:\n")
            f.write("-" * 25 + "\n")
            f.write("- Автоматическая категоризация новых отзывов\n")
            f.write("- Мониторинг настроений по конкретным продуктам\n")
            f.write("- Выявление проблемных областей в банковском обслуживании\n")
            f.write("- Персонализация коммуникации с клиентами\n")
            f.write("- Улучшение продуктовой линейки на основе обратной связи\n")
        
        print("Итоговый отчет сохранен")

def main():
    """Основная функция"""
    # Пути к данным
    data_path = '/Users/mishantique/Desktop/Projects/gazprombank_hachaton/data/raw/sravni_ru/sravni_ru.json'
    
    results_paths = {
        'embedding_clustering': '/Users/mishantique/Desktop/Projects/gazprombank_hachaton/data/processed/embedding_clustering_results.json',
        'topic_modeling': '/Users/mishantique/Desktop/Projects/gazprombank_hachaton/data/processed/topic_modeling_results.json',
        'tfidf_clustering': '/Users/mishantique/Desktop/Projects/gazprombank_hachaton/data/processed/tfidf_clustering_results.json'
    }
    
    # Создаем объект для оценки
    evaluation = ClusteringEvaluation(data_path)
    
    # Выполняем оценку
    evaluation.load_original_data()
    evaluation.load_clustering_results(results_paths)
    
    # Анализируем результаты
    consistency_results = evaluation.analyze_cluster_consistency()
    alignment_results = evaluation.analyze_product_type_alignment()
    profiles = evaluation.create_cluster_profiles()
    quality_metrics = evaluation.evaluate_clustering_quality()
    
    # Создаем визуализации и рекомендации
    evaluation.create_summary_visualization(quality_metrics)
    recommendations = evaluation.generate_recommendations(quality_metrics, alignment_results)
    
    # Сохраняем итоговый отчет
    output_path = '/Users/mishantique/Desktop/Projects/gazprombank_hachaton/reports/clustering_evaluation_report.txt'
    evaluation.save_evaluation_report(quality_metrics, alignment_results, recommendations, output_path)
    
    print("\nОценка методов кластеризации завершена!")
    print("Все результаты сохранены в папке reports/")

if __name__ == "__main__":
    main()
