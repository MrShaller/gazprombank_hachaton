#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Кластеризация отзывов на основе эмбеддингов (BERT/sentence-transformers)

Этот скрипт выполняет семантическую кластеризацию текстов отзывов 
с использованием предварительно обученных трансформерных моделей.
"""

import json
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from sentence_transformers import SentenceTransformer
import re
import warnings
warnings.filterwarnings('ignore')

class EmbeddingClustering:
    def __init__(self, data_path):
        """
        Инициализация класса для кластеризации на основе эмбеддингов
        
        Args:
            data_path (str): Путь к JSON файлу с данными
        """
        self.data_path = data_path
        self.data = None
        self.embeddings = None
        self.model = None
        self.clusters = None
        
    def load_data(self, max_samples=40000):
        """Загрузка данных из JSON файла с ограничением размера выборки"""
        print("Загружаем данные...")
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        # Преобразуем в DataFrame для удобства
        self.df = pd.DataFrame(self.data)
        
        # Ограничиваем размер выборки для избежания проблем с памятью
        if len(self.df) > max_samples:
            print(f"Данных слишком много ({len(self.df)}), берем случайную выборку из {max_samples} отзывов")
            self.df = self.df.sample(n=max_samples, random_state=42).reset_index(drop=True)
        
        print(f"Загружено {len(self.df)} отзывов")
        
    def preprocess_text(self, text):
        """
        Предобработка текста
        
        Args:
            text (str): Исходный текст
            
        Returns:
            str: Обработанный текст
        """
        if not text:
            return ""
            
        # Убираем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Убираем email адреса
        text = re.sub(r'\S*@\S*\s?', '', text)
        
        # Убираем URL
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        return text
    
    def load_model(self, model_name='cointegrated/rubert-tiny2'):
        """
        Загрузка модели для создания эмбеддингов
        
        Args:
            model_name (str): Название модели
        """
        print(f"Загружаем модель {model_name}...")
        # Используем CPU для избежания проблем с Metal на macOS
        self.model = SentenceTransformer(model_name, device='cpu')
        print("Модель загружена")
        
    def create_embeddings(self, batch_size=32):
        """Создание эмбеддингов для текстов отзывов с батчевой обработкой"""
        print("Создаем эмбеддинги...")
        
        # Предобработка текстов
        texts = [self.preprocess_text(str(review)) for review in self.df['review_text']]
        
        # Создаем эмбеддинги с небольшим размером батча
        self.embeddings = self.model.encode(
            texts, 
            show_progress_bar=True, 
            batch_size=batch_size,
            convert_to_numpy=True
        )
        print(f"Создано {len(self.embeddings)} эмбеддингов размерности {self.embeddings.shape[1]}")
        
    def find_optimal_clusters(self, max_clusters=20):
        """
        Поиск оптимального количества кластеров с помощью метода локтя и silhouette score
        
        Args:
            max_clusters (int): Максимальное количество кластеров для тестирования
            
        Returns:
            int: Оптимальное количество кластеров
        """
        print("Ищем оптимальное количество кластеров...")
        
        inertias = []
        silhouette_scores = []
        k_range = range(2, max_clusters + 1)
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(self.embeddings)
            
            inertias.append(kmeans.inertia_)
            silhouette_scores.append(silhouette_score(self.embeddings, cluster_labels))
            
        # Визуализация результатов
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # График метода локтя
        ax1.plot(k_range, inertias, 'bo-')
        ax1.set_xlabel('Количество кластеров')
        ax1.set_ylabel('Инерция')
        ax1.set_title('Метод локтя')
        ax1.grid(True)
        
        # График silhouette score
        ax2.plot(k_range, silhouette_scores, 'ro-')
        ax2.set_xlabel('Количество кластеров')
        ax2.set_ylabel('Silhouette Score')
        ax2.set_title('Silhouette Score')
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig('/Users/mishantique/Desktop/Projects/gazprombank_hachaton/reports/clustering/embedding_cluster_optimization.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
        
        # Находим оптимальное количество кластеров (максимальный silhouette score)
        optimal_k = k_range[np.argmax(silhouette_scores)]
        print(f"Оптимальное количество кластеров: {optimal_k} (Silhouette Score: {max(silhouette_scores):.3f})")
        
        return optimal_k
    
    def perform_clustering(self, n_clusters=None):
        """
        Выполнение кластеризации
        
        Args:
            n_clusters (int): Количество кластеров (если None, то автоматически определяется)
        """
        if n_clusters is None:
            n_clusters = self.find_optimal_clusters()
        
        print(f"Выполняем кластеризацию на {n_clusters} кластеров...")
        
        # K-means кластеризация
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.clusters = kmeans.fit_predict(self.embeddings)
        
        # Добавляем результаты кластеризации в DataFrame
        self.df['cluster'] = self.clusters
        
        # Вычисляем silhouette score
        silhouette_avg = silhouette_score(self.embeddings, self.clusters)
        print(f"Средний silhouette score: {silhouette_avg:.3f}")
        
        return kmeans
    
    def analyze_clusters(self):
        """Анализ полученных кластеров"""
        print("\nАнализ кластеров:")
        print("=" * 50)
        
        cluster_info = []
        
        for cluster_id in sorted(self.df['cluster'].unique()):
            cluster_data = self.df[self.df['cluster'] == cluster_id]
            
            # Статистика по кластеру
            cluster_size = len(cluster_data)
            
            # Наиболее частые типы продуктов в кластере
            top_products = cluster_data['product_type'].value_counts().head(3)
            
            # Средняя длина текста
            avg_length = cluster_data['review_text'].str.len().mean()
            
            # Примеры текстов (самые короткие для читаемости)
            if len(cluster_data) > 0:
                # Создаем временный DataFrame с длиной текста
                cluster_with_length = cluster_data.copy()
                cluster_with_length['text_length'] = cluster_with_length['review_text'].str.len()
                examples_df = cluster_with_length.nsmallest(min(3, len(cluster_data)), 'text_length')
                examples = examples_df['review_text'].tolist()
            else:
                examples = []
            
            cluster_info.append({
                'cluster_id': cluster_id,
                'size': cluster_size,
                'percentage': (cluster_size / len(self.df)) * 100,
                'top_products': top_products.to_dict(),
                'avg_length': avg_length,
                'examples': examples
            })
            
            print(f"\nКластер {cluster_id}:")
            print(f"  Размер: {cluster_size} отзывов ({cluster_size/len(self.df)*100:.1f}%)")
            print(f"  Основные продукты: {dict(top_products.head(3))}")
            print(f"  Средняя длина текста: {avg_length:.0f} символов")
            print(f"  Примеры отзывов:")
            for i, example in enumerate(examples[:2]):
                print(f"    {i+1}. {example[:200]}...")
        
        return cluster_info
    
    def visualize_clusters(self):
        """Визуализация кластеров с помощью PCA"""
        print("Создаем визуализацию кластеров...")
        
        # Уменьшение размерности с помощью PCA
        pca = PCA(n_components=2, random_state=42)
        embeddings_2d = pca.fit_transform(self.embeddings)
        
        # Создание графика
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], 
                            c=self.clusters, cmap='tab20', alpha=0.6)
        plt.colorbar(scatter)
        plt.title('Визуализация кластеров (PCA)', fontsize=16)
        plt.xlabel(f'Первая главная компонента (объясняет {pca.explained_variance_ratio_[0]:.1%} вариации)')
        plt.ylabel(f'Вторая главная компонента (объясняет {pca.explained_variance_ratio_[1]:.1%} вариации)')
        
        # Добавляем центроиды кластеров
        for cluster_id in range(len(np.unique(self.clusters))):
            cluster_center = embeddings_2d[self.clusters == cluster_id].mean(axis=0)
            plt.annotate(f'Кластер {cluster_id}', 
                        xy=cluster_center, 
                        xytext=(5, 5), 
                        textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7),
                        fontsize=10, fontweight='bold')
        
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('/Users/mishantique/Desktop/Projects/gazprombank_hachaton/reports/clustering/embedding_clusters_visualization.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
    
    def save_results(self, output_path):
        """
        Сохранение результатов кластеризации
        
        Args:
            output_path (str): Путь для сохранения результатов
        """
        print(f"Сохраняем результаты в {output_path}...")
        
        # Сохраняем DataFrame с результатами кластеризации
        self.df.to_json(output_path, orient='records', indent=2)
        
        # Сохраняем сводную статистику
        summary_path = output_path.replace('.json', '_summary.txt')
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("РЕЗУЛЬТАТЫ КЛАСТЕРИЗАЦИИ НА ОСНОВЕ ЭМБЕДДИНГОВ\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Общее количество отзывов: {len(self.df)}\n")
            f.write(f"Количество кластеров: {len(self.df['cluster'].unique())}\n")
            f.write(f"Silhouette Score: {silhouette_score(self.embeddings, self.clusters):.3f}\n\n")
            
            # Статистика по кластерам
            for cluster_id in sorted(self.df['cluster'].unique()):
                cluster_data = self.df[self.df['cluster'] == cluster_id]
                f.write(f"Кластер {cluster_id}:\n")
                f.write(f"  Размер: {len(cluster_data)} отзывов\n")
                f.write(f"  Основные продукты:\n")
                for product, count in cluster_data['product_type'].value_counts().head(5).items():
                    f.write(f"    {product}: {count}\n")
                f.write("\n")
        
        print("Результаты сохранены")

def main():
    """Основная функция"""
    # Путь к данным
    data_path = '/Users/mishantique/Desktop/Projects/gazprombank_hachaton/data/raw/sravni_ru/sravni_ru.json'
    
    # Создаем объект для кластеризации
    clustering = EmbeddingClustering(data_path)
    
    # Выполняем кластеризацию
    clustering.load_data()
    clustering.load_model()
    clustering.create_embeddings()
    clustering.perform_clustering()
    
    # Анализируем результаты
    cluster_info = clustering.analyze_clusters()
    clustering.visualize_clusters()
    
    # Сохраняем результаты
    output_path = '/Users/mishantique/Desktop/Projects/gazprombank_hachaton/data/processed/embedding_clustering_results.json'
    clustering.save_results(output_path)
    
    print("\nКластеризация на основе эмбеддингов завершена!")

if __name__ == "__main__":
    main()
