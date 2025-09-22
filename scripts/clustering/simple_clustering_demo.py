#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простая демонстрация кластеризации отзывов

Упрощенная версия для быстрого тестирования основных методов кластеризации.
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from collections import Counter
import re
import warnings
warnings.filterwarnings('ignore')

def load_data(data_path, sample_size=1000):
    """Загрузка и выборка данных"""
    print(f"Загружаем данные из {data_path}...")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    # Берем выборку для быстрой демонстрации
    if len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42)
        print(f"Используем выборку из {sample_size} отзывов")
    
    print(f"Загружено {len(df)} отзывов")
    return df

def preprocess_text(text):
    """Простая предобработка текста"""
    if not text:
        return ""
    
    # Приводим к нижнему регистру
    text = text.lower()
    
    # Убираем специальные символы и цифры
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\d+', '', text)
    
    # Убираем лишние пробелы
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def analyze_data(df):
    """Анализ исходных данных"""
    print("\n=== АНАЛИЗ ДАННЫХ ===")
    
    # Распределение по типам продуктов
    product_counts = df['product_type'].value_counts()
    print(f"\nТоп-5 типов продуктов:")
    for product, count in product_counts.head(5).items():
        print(f"  {product}: {count}")
    
    # Статистика длины текстов
    text_lengths = df['review_text'].str.len()
    print(f"\nДлина текстов:")
    print(f"  Средняя: {text_lengths.mean():.0f} символов")
    print(f"  Медиана: {text_lengths.median():.0f} символов")
    print(f"  Минимум: {text_lengths.min()}")
    print(f"  Максимум: {text_lengths.max()}")
    
    return product_counts

def simple_tfidf_clustering(df, n_clusters=8):
    """Простая TF-IDF кластеризация"""
    print(f"\n=== TF-IDF КЛАСТЕРИЗАЦИЯ ===")
    print(f"Целевое количество кластеров: {n_clusters}")
    
    # Предобработка текстов
    print("Предобрабатываем тексты...")
    processed_texts = df['review_text'].apply(preprocess_text)
    
    # Убираем пустые тексты
    valid_mask = processed_texts.str.len() > 10
    processed_texts = processed_texts[valid_mask].reset_index(drop=True)
    df_clean = df[valid_mask].copy().reset_index(drop=True)
    
    print(f"После предобработки: {len(processed_texts)} текстов")
    
    # TF-IDF векторизация
    print("Создаем TF-IDF векторы...")
    vectorizer = TfidfVectorizer(
        max_features=1000,
        min_df=2,
        max_df=0.8,
        ngram_range=(1, 2),
        stop_words=None  # Используем простой подход без стоп-слов
    )
    
    tfidf_matrix = vectorizer.fit_transform(processed_texts)
    print(f"Создана TF-IDF матрица размера: {tfidf_matrix.shape}")
    
    # K-means кластеризация
    print("Выполняем кластеризацию...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(tfidf_matrix)
    
    # Добавляем результаты в DataFrame
    df_clean['cluster'] = clusters
    
    # Вычисляем метрики
    silhouette_avg = silhouette_score(tfidf_matrix, clusters)
    print(f"Silhouette Score: {silhouette_avg:.3f}")
    
    return df_clean, clusters, tfidf_matrix, vectorizer

def analyze_clusters(df_clustered, vectorizer):
    """Анализ полученных кластеров"""
    print(f"\n=== АНАЛИЗ КЛАСТЕРОВ ===")
    
    for cluster_id in sorted(df_clustered['cluster'].unique()):
        cluster_data = df_clustered[df_clustered['cluster'] == cluster_id]
        cluster_size = len(cluster_data)
        
        print(f"\nКластер {cluster_id} ({cluster_size} отзывов):")
        
        # Топ продукты в кластере
        top_products = cluster_data['product_type'].value_counts().head(3)
        print(f"  Основные продукты: {dict(top_products)}")
        
        # Средняя длина текста
        avg_length = cluster_data['review_text'].str.len().mean()
        print(f"  Средняя длина: {avg_length:.0f} символов")
        
        # Примеры коротких отзывов для читаемости
        if len(cluster_data) > 0:
            # Создаем временный DataFrame с длиной текста
            cluster_with_length = cluster_data.copy()
            cluster_with_length['text_length'] = cluster_with_length['review_text'].str.len()
            examples = cluster_with_length.nsmallest(min(2, len(cluster_data)), 'text_length')
            
            print(f"  Примеры отзывов:")
            for i, (_, row) in enumerate(examples.iterrows()):
                text = row['review_text'][:150] + "..." if len(row['review_text']) > 150 else row['review_text']
                print(f"    {i+1}. {text}")
        else:
            print(f"  Примеры отзывов: нет данных")

def visualize_clusters(df_clustered, tfidf_matrix):
    """Визуализация кластеров"""
    print(f"\n=== ВИЗУАЛИЗАЦИЯ ===")
    
    # Уменьшение размерности с помощью PCA
    print("Создаем 2D визуализацию...")
    pca = PCA(n_components=2, random_state=42)
    coords_2d = pca.fit_transform(tfidf_matrix.toarray())
    
    # График
    plt.figure(figsize=(12, 8))
    scatter = plt.scatter(coords_2d[:, 0], coords_2d[:, 1], 
                         c=df_clustered['cluster'], cmap='tab10', alpha=0.6)
    plt.colorbar(scatter)
    plt.title('Визуализация кластеров (PCA)', fontsize=16)
    plt.xlabel(f'Первая главная компонента ({pca.explained_variance_ratio_[0]:.1%} вариации)')
    plt.ylabel(f'Вторая главная компонента ({pca.explained_variance_ratio_[1]:.1%} вариации)')
    
    # Добавляем центроиды
    for cluster_id in df_clustered['cluster'].unique():
        cluster_center = coords_2d[df_clustered['cluster'] == cluster_id].mean(axis=0)
        plt.annotate(f'Кластер {cluster_id}', 
                    xy=cluster_center, 
                    xytext=(5, 5), 
                    textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8),
                    fontsize=10, fontweight='bold')
    
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Сохраняем график
    import os
    os.makedirs('/Users/mishantique/Desktop/Projects/gazprombank_hachaton/reports/clustering', exist_ok=True)
    output_path = '/Users/mishantique/Desktop/Projects/gazprombank_hachaton/reports/clustering/simple_clustering_demo.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"График сохранен: {output_path}")
    plt.show()

def create_summary_report(df_clustered, original_product_counts):
    """Создание краткого отчета"""
    print(f"\n=== КРАТКИЙ ОТЧЕТ ===")
    
    # Общая статистика
    n_clusters = len(df_clustered['cluster'].unique())
    total_reviews = len(df_clustered)
    
    print(f"Общее количество отзывов: {total_reviews}")
    print(f"Количество кластеров: {n_clusters}")
    print(f"Средний размер кластера: {total_reviews/n_clusters:.1f}")
    
    # Соответствие кластеров продуктам
    print(f"\nСоответствие кластеров типам продуктов:")
    cluster_product_match = {}
    
    for cluster_id in sorted(df_clustered['cluster'].unique()):
        cluster_data = df_clustered[df_clustered['cluster'] == cluster_id]
        dominant_product = cluster_data['product_type'].value_counts().index[0]
        dominant_count = cluster_data['product_type'].value_counts().iloc[0]
        purity = dominant_count / len(cluster_data)
        
        cluster_product_match[cluster_id] = {
            'product': dominant_product,
            'purity': purity,
            'size': len(cluster_data)
        }
        
        print(f"  Кластер {cluster_id}: {dominant_product} ({purity:.1%} чистоты, {len(cluster_data)} отзывов)")
    
    # Общая чистота
    avg_purity = np.mean([info['purity'] for info in cluster_product_match.values()])
    print(f"\nСредняя чистота кластеров: {avg_purity:.1%}")
    
    if avg_purity > 0.6:
        print("✅ Хорошее качество кластеризации")
    elif avg_purity > 0.4:
        print("⚠️  Средняее качество кластеризации")
    else:
        print("❌ Низкое качество кластеризации")
    
    return cluster_product_match

def main():
    """Основная функция демонстрации"""
    print("🚀 ДЕМОНСТРАЦИЯ КЛАСТЕРИЗАЦИИ ОТЗЫВОВ БАНКА")
    print("=" * 60)
    
    # Путь к данным
    data_path = '/Users/mishantique/Desktop/Projects/gazprombank_hachaton/data/raw/sravni_ru/sravni_ru.json'
    
    try:
        # 1. Загрузка данных
        df = load_data(data_path, sample_size=1000)  # Берем выборку для демо
        
        # 2. Анализ данных
        product_counts = analyze_data(df)
        
        # 3. Кластеризация
        df_clustered, clusters, tfidf_matrix, vectorizer = simple_tfidf_clustering(df, n_clusters=8)
        
        # 4. Анализ кластеров
        analyze_clusters(df_clustered, vectorizer)
        
        # 5. Визуализация
        visualize_clusters(df_clustered, tfidf_matrix)
        
        # 6. Отчет
        cluster_info = create_summary_report(df_clustered, product_counts)
        
        print(f"\n✅ Демонстрация завершена успешно!")
        print(f"📊 Результаты сохранены в папке reports/")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
