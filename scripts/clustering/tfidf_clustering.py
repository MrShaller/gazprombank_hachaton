#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Кластеризация отзывов на основе TF-IDF и K-means

Этот скрипт выполняет кластеризацию текстов отзывов 
с использованием TF-IDF векторизации и различных алгоритмов кластеризации.
"""

import json
import numpy as np
import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# Фикс для совместимости с новыми версиями Python
import inspect
if not hasattr(inspect, 'getargspec'):
    def getargspec_fix(func):
        spec = inspect.getfullargspec(func)
        return spec.args, spec.varargs, spec.varkw, spec.defaults
    inspect.getargspec = getargspec_fix

# Для TF-IDF и кластеризации
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.preprocessing import StandardScaler

# Для предобработки текста
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import pymorphy2

# Для визуализации
from wordcloud import WordCloud

class TfIdfClustering:
    def __init__(self, data_path):
        """
        Инициализация класса для TF-IDF кластеризации
        
        Args:
            data_path (str): Путь к JSON файлу с данными
        """
        self.data_path = data_path
        self.data = None
        self.df = None
        self.processed_texts = None
        self.tfidf_matrix = None
        self.vectorizer = None
        self.morph = pymorphy2.MorphAnalyzer()
        
        # Загружаем стоп-слова
        try:
            self.stop_words = set(stopwords.words('russian'))
        except LookupError:
            nltk.download('stopwords')
            nltk.download('punkt')
            self.stop_words = set(stopwords.words('russian'))
        
        # Добавляем специфичные стоп-слова
        banking_stopwords = {
            'банк', 'банка', 'банке', 'банком', 'банки', 'банков', 'банкам', 'банками',
            'газпромбанк', 'газпром', 'гпб', 'отзыв', 'отзыва', 'отзывы', 'отзывов',
            'клиент', 'клиента', 'клиенты', 'клиентов', 'сервис', 'услуга', 'услуги',
            'год', 'года', 'лет', 'месяц', 'месяца', 'месяцев', 'день', 'дня', 'дней',
            'рубль', 'рубля', 'рублей', 'тысяча', 'тысяч', 'миллион', 'миллионов',
            'хороший', 'плохой', 'хорошо', 'плохо', 'очень', 'просто', 'можно', 'нужно'
        }
        self.stop_words.update(banking_stopwords)
        
    def load_data(self, max_samples=40000):
        """Загрузка данных из JSON файла с ограничением размера выборки"""
        print("Загружаем данные...")
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        self.df = pd.DataFrame(self.data)
        
        # Ограничиваем размер выборки для избежания проблем с памятью
        if len(self.df) > max_samples:
            print(f"Данных слишком много ({len(self.df)}), берем случайную выборку из {max_samples} отзывов")
            self.df = self.df.sample(n=max_samples, random_state=42).reset_index(drop=True)
            self.data = self.df.to_dict('records')
        
        print(f"Загружено {len(self.df)} отзывов")
        
    def preprocess_text(self, text):
        """
        Предобработка текста для TF-IDF
        
        Args:
            text (str): Исходный текст
            
        Returns:
            str: Обработанный текст
        """
        if not text:
            return ""
        
        # Приводим к нижнему регистру
        text = text.lower()
        
        # Убираем специальные символы, оставляем только буквы
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', '', text)
        
        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Токенизация
        try:
            tokens = word_tokenize(text, language='russian')
        except LookupError:
            tokens = text.split()
        
        # Лемматизация и фильтрация
        processed_tokens = []
        for token in tokens:
            if len(token) > 2 and token not in self.stop_words:
                # Лемматизация с помощью pymorphy2
                lemma = self.morph.parse(token)[0].normal_form
                if lemma not in self.stop_words and len(lemma) > 2:
                    processed_tokens.append(lemma)
        
        return ' '.join(processed_tokens)
    
    def prepare_texts(self):
        """Предобработка всех текстов"""
        print("Предобрабатываем тексты...")
        self.processed_texts = []
        
        for review in self.data:
            processed = self.preprocess_text(review['review_text'])
            self.processed_texts.append(processed)
        
        # Убираем пустые тексты
        valid_indices = [i for i, text in enumerate(self.processed_texts) if text.strip()]
        self.processed_texts = [self.processed_texts[i] for i in valid_indices]
        self.df = self.df.iloc[valid_indices].reset_index(drop=True)
        
        print(f"После предобработки осталось {len(self.processed_texts)} текстов")
    
    def create_tfidf_matrix(self, max_features=5000, ngram_range=(1, 2)):
        """
        Создание TF-IDF матрицы
        
        Args:
            max_features (int): Максимальное количество признаков
            ngram_range (tuple): Диапазон n-грамм
        """
        print("Создаем TF-IDF матрицу...")
        
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            min_df=5,
            max_df=0.8,
            stop_words=list(self.stop_words),
            sublinear_tf=True
        )
        
        self.tfidf_matrix = self.vectorizer.fit_transform(self.processed_texts)
        
        print(f"Создана TF-IDF матрица размера {self.tfidf_matrix.shape}")
        
        # Показываем топ слова по TF-IDF
        feature_names = self.vectorizer.get_feature_names_out()
        tfidf_scores = self.tfidf_matrix.mean(axis=0).A1
        top_words_indices = tfidf_scores.argsort()[-20:][::-1]
        
        print("Топ-20 слов по средней TF-IDF важности:")
        for i, idx in enumerate(top_words_indices):
            print(f"  {i+1}. {feature_names[idx]}: {tfidf_scores[idx]:.4f}")
    
    def find_optimal_clusters(self, max_clusters=25, algorithm='kmeans'):
        """
        Поиск оптимального количества кластеров
        
        Args:
            max_clusters (int): Максимальное количество кластеров
            algorithm (str): Алгоритм кластеризации ('kmeans', 'agglomerative')
            
        Returns:
            int: Оптимальное количество кластеров
        """
        print(f"Ищем оптимальное количество кластеров для {algorithm}...")
        
        # Уменьшаем размерность для ускорения вычислений
        if self.tfidf_matrix.shape[1] > 1000:
            print("Уменьшаем размерность с помощью TruncatedSVD...")
            svd = TruncatedSVD(n_components=500, random_state=42)
            X = svd.fit_transform(self.tfidf_matrix)
        else:
            X = self.tfidf_matrix.toarray()
        
        inertias = []
        silhouette_scores = []
        calinski_scores = []
        davies_bouldin_scores = []
        
        k_range = range(2, min(max_clusters + 1, len(self.processed_texts) // 10))
        
        for k in k_range:
            print(f"  Тестируем {k} кластеров...")
            
            if algorithm == 'kmeans':
                clusterer = KMeans(n_clusters=k, random_state=42, n_init=10)
            elif algorithm == 'agglomerative':
                clusterer = AgglomerativeClustering(n_clusters=k, linkage='ward')
            else:
                raise ValueError(f"Неизвестный алгоритм: {algorithm}")
            
            cluster_labels = clusterer.fit_predict(X)
            
            # Вычисляем метрики
            if algorithm == 'kmeans':
                inertias.append(clusterer.inertia_)
            
            silhouette_avg = silhouette_score(X, cluster_labels)
            calinski_score = calinski_harabasz_score(X, cluster_labels)
            davies_bouldin_score_val = davies_bouldin_score(X, cluster_labels)
            
            silhouette_scores.append(silhouette_avg)
            calinski_scores.append(calinski_score)
            davies_bouldin_scores.append(davies_bouldin_score_val)
        
        # Визуализация метрик
        n_metrics = 3 if algorithm == 'kmeans' else 3
        fig, axes = plt.subplots(1, n_metrics, figsize=(15, 5))
        
        if algorithm == 'kmeans':
            axes[0].plot(k_range, inertias, 'bo-')
            axes[0].set_xlabel('Количество кластеров')
            axes[0].set_ylabel('Инерция')
            axes[0].set_title('Метод локтя')
            axes[0].grid(True)
            
            axes[1].plot(k_range, silhouette_scores, 'ro-')
            axes[1].set_xlabel('Количество кластеров')
            axes[1].set_ylabel('Silhouette Score')
            axes[1].set_title('Silhouette Score')
            axes[1].grid(True)
            
            axes[2].plot(k_range, calinski_scores, 'go-')
            axes[2].set_xlabel('Количество кластеров')
            axes[2].set_ylabel('Calinski-Harabasz Score')
            axes[2].set_title('Calinski-Harabasz Score')
            axes[2].grid(True)
        else:
            axes[0].plot(k_range, silhouette_scores, 'ro-')
            axes[0].set_xlabel('Количество кластеров')
            axes[0].set_ylabel('Silhouette Score')
            axes[0].set_title('Silhouette Score')
            axes[0].grid(True)
            
            axes[1].plot(k_range, calinski_scores, 'go-')
            axes[1].set_xlabel('Количество кластеров')
            axes[1].set_ylabel('Calinski-Harabasz Score')
            axes[1].set_title('Calinski-Harabasz Score')
            axes[1].grid(True)
            
            axes[2].plot(k_range, davies_bouldin_scores, 'mo-')
            axes[2].set_xlabel('Количество кластеров')
            axes[2].set_ylabel('Davies-Bouldin Score')
            axes[2].set_title('Davies-Bouldin Score (меньше = лучше)')
            axes[2].grid(True)
        
        plt.tight_layout()
        plt.savefig(f'/Users/mishantique/Desktop/Projects/gazprombank_hachaton/reports/clustering/tfidf_{algorithm}_optimization.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
        
        # Выбираем оптимальное количество кластеров на основе silhouette score
        optimal_k = k_range[np.argmax(silhouette_scores)]
        print(f"Оптимальное количество кластеров: {optimal_k}")
        print(f"  Silhouette Score: {max(silhouette_scores):.3f}")
        print(f"  Calinski-Harabasz Score: {calinski_scores[np.argmax(silhouette_scores)]:.3f}")
        
        return optimal_k, X
    
    def perform_clustering(self, n_clusters=None, algorithms=['kmeans', 'agglomerative', 'dbscan']):
        """
        Выполнение кластеризации различными алгоритмами
        
        Args:
            n_clusters (int): Количество кластеров
            algorithms (list): Список алгоритмов для использования
            
        Returns:
            dict: Результаты кластеризации
        """
        results = {}
        
        for algorithm in algorithms:
            print(f"\nВыполняем кластеризацию алгоритмом {algorithm}...")
            
            if algorithm in ['kmeans', 'agglomerative'] and n_clusters is None:
                optimal_k, X = self.find_optimal_clusters(algorithm=algorithm)
            else:
                # Подготавливаем данные
                if self.tfidf_matrix.shape[1] > 1000:
                    svd = TruncatedSVD(n_components=500, random_state=42)
                    X = svd.fit_transform(self.tfidf_matrix)
                else:
                    X = self.tfidf_matrix.toarray()
                optimal_k = n_clusters if n_clusters else 10
            
            # Выполняем кластеризацию
            if algorithm == 'kmeans':
                clusterer = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
                cluster_labels = clusterer.fit_predict(X)
                
            elif algorithm == 'agglomerative':
                clusterer = AgglomerativeClustering(n_clusters=optimal_k, linkage='ward')
                cluster_labels = clusterer.fit_predict(X)
                
            elif algorithm == 'dbscan':
                # Для DBSCAN подбираем параметры
                clusterer = DBSCAN(eps=0.5, min_samples=5, metric='cosine')
                cluster_labels = clusterer.fit_predict(X)
                optimal_k = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
                print(f"  DBSCAN нашел {optimal_k} кластеров")
            
            # Добавляем результаты в DataFrame
            self.df[f'{algorithm}_cluster'] = cluster_labels
            
            # Анализируем результаты
            cluster_analysis = self._analyze_clusters(cluster_labels, algorithm)
            
            # Вычисляем метрики качества
            if len(set(cluster_labels)) > 1:
                silhouette_avg = silhouette_score(X, cluster_labels)
                calinski_score = calinski_harabasz_score(X, cluster_labels)
                davies_bouldin_score_val = davies_bouldin_score(X, cluster_labels)
            else:
                silhouette_avg = calinski_score = davies_bouldin_score_val = 0
            
            results[algorithm] = {
                'clusterer': clusterer,
                'cluster_labels': cluster_labels,
                'n_clusters': optimal_k,
                'silhouette_score': silhouette_avg,
                'calinski_score': calinski_score,
                'davies_bouldin_score': davies_bouldin_score_val,
                'cluster_analysis': cluster_analysis
            }
            
            print(f"  Количество кластеров: {optimal_k}")
            print(f"  Silhouette Score: {silhouette_avg:.3f}")
            print(f"  Calinski-Harabasz Score: {calinski_score:.3f}")
            print(f"  Davies-Bouldin Score: {davies_bouldin_score_val:.3f}")
        
        return results
    
    def _analyze_clusters(self, cluster_labels, algorithm):
        """Анализ кластеров"""
        print(f"\nАнализ кластеров ({algorithm}):")
        print("=" * 50)
        
        cluster_info = []
        unique_clusters = sorted(set(cluster_labels))
        
        for cluster_id in unique_clusters:
            if cluster_id == -1:  # Outliers в DBSCAN
                cluster_name = "Outliers"
            else:
                cluster_name = f"Кластер {cluster_id}"
            
            cluster_mask = cluster_labels == cluster_id
            cluster_data = self.df[cluster_mask]
            cluster_texts = [self.processed_texts[i] for i, mask in enumerate(cluster_mask) if mask]
            
            # Статистика по кластеру
            cluster_size = len(cluster_data)
            
            # Наиболее частые типы продуктов
            top_products = cluster_data['product_type'].value_counts().head(3)
            
            # Ключевые слова кластера
            if cluster_texts:
                cluster_tfidf = self.vectorizer.transform(cluster_texts)
                cluster_scores = cluster_tfidf.mean(axis=0).A1
                feature_names = self.vectorizer.get_feature_names_out()
                top_words_indices = cluster_scores.argsort()[-10:][::-1]
                top_words = [(feature_names[idx], cluster_scores[idx]) for idx in top_words_indices]
            else:
                top_words = []
            
            # Средняя длина текста
            avg_length = cluster_data['review_text'].str.len().mean()
            
            cluster_info.append({
                'cluster_id': cluster_id,
                'cluster_name': cluster_name,
                'size': cluster_size,
                'percentage': (cluster_size / len(self.df)) * 100,
                'top_products': top_products.to_dict(),
                'top_words': top_words,
                'avg_length': avg_length
            })
            
            print(f"\n{cluster_name}:")
            print(f"  Размер: {cluster_size} отзывов ({cluster_size/len(self.df)*100:.1f}%)")
            print(f"  Основные продукты: {dict(top_products.head(3))}")
            print(f"  Ключевые слова: {', '.join([word for word, _ in top_words[:5]])}")
            print(f"  Средняя длина текста: {avg_length:.0f} символов")
        
        return cluster_info
    
    def create_word_clouds(self, results):
        """Создание облаков слов для кластеров"""
        print("Создаем облака слов для кластеров...")
        
        for algorithm, result in results.items():
            cluster_labels = result['cluster_labels']
            unique_clusters = sorted(set(cluster_labels))
            
            n_clusters = len([c for c in unique_clusters if c != -1])
            if n_clusters == 0:
                continue
                
            fig, axes = plt.subplots((n_clusters + 2) // 3, 3, figsize=(15, 5 * ((n_clusters + 2) // 3)))
            if n_clusters == 1:
                axes = [axes]
            elif (n_clusters + 2) // 3 == 1:
                axes = axes.flatten()
            else:
                axes = axes.flatten()
            
            plot_idx = 0
            for cluster_id in unique_clusters:
                if cluster_id == -1:  # Пропускаем outliers
                    continue
                    
                cluster_mask = cluster_labels == cluster_id
                cluster_texts = [self.processed_texts[i] for i, mask in enumerate(cluster_mask) if mask]
                
                if cluster_texts:
                    # Объединяем все тексты кластера
                    cluster_text = ' '.join(cluster_texts)
                    
                    # Создаем облако слов
                    wordcloud = WordCloud(
                        width=400, height=300,
                        background_color='white',
                        max_words=50,
                        font_path=None,  # Используем системный шрифт
                        colormap='viridis'
                    ).generate(cluster_text)
                    
                    axes[plot_idx].imshow(wordcloud, interpolation='bilinear')
                    axes[plot_idx].set_title(f'Кластер {cluster_id} ({sum(cluster_mask)} отзывов)')
                    axes[plot_idx].axis('off')
                    plot_idx += 1
            
            # Убираем пустые субплоты
            for i in range(plot_idx, len(axes)):
                axes[i].axis('off')
            
            plt.tight_layout()
            plt.savefig(f'/Users/mishantique/Desktop/Projects/gazprombank_hachaton/reports/clustering/tfidf_{algorithm}_wordclouds.png', 
                       dpi=300, bbox_inches='tight')
            plt.show()
    
    def visualize_clusters(self, results):
        """Визуализация кластеров с помощью PCA"""
        print("Создаем визуализацию кластеров...")
        
        # Уменьшение размерности с помощью PCA
        if self.tfidf_matrix.shape[1] > 1000:
            svd = TruncatedSVD(n_components=100, random_state=42)
            X_reduced = svd.fit_transform(self.tfidf_matrix)
        else:
            X_reduced = self.tfidf_matrix.toarray()
        
        pca = PCA(n_components=2, random_state=42)
        X_2d = pca.fit_transform(X_reduced)
        
        # Создаем визуализацию для каждого алгоритма
        n_algorithms = len(results)
        fig, axes = plt.subplots(1, n_algorithms, figsize=(6 * n_algorithms, 6))
        
        if n_algorithms == 1:
            axes = [axes]
        
        for idx, (algorithm, result) in enumerate(results.items()):
            cluster_labels = result['cluster_labels']
            
            scatter = axes[idx].scatter(X_2d[:, 0], X_2d[:, 1], 
                                     c=cluster_labels, cmap='tab20', alpha=0.6)
            axes[idx].set_title(f'{algorithm.upper()}\n'
                              f'Silhouette: {result["silhouette_score"]:.3f}')
            axes[idx].set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%})')
            axes[idx].set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%})')
            axes[idx].grid(True, alpha=0.3)
            
            # Добавляем центроиды кластеров (кроме DBSCAN outliers)
            unique_clusters = set(cluster_labels)
            if -1 in unique_clusters:
                unique_clusters.remove(-1)
            
            for cluster_id in unique_clusters:
                cluster_center = X_2d[cluster_labels == cluster_id].mean(axis=0)
                axes[idx].annotate(f'{cluster_id}', 
                                 xy=cluster_center, 
                                 xytext=(5, 5), 
                                 textcoords='offset points',
                                 bbox=dict(boxstyle='round,pad=0.3', 
                                         facecolor='white', alpha=0.7),
                                 fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('/Users/mishantique/Desktop/Projects/gazprombank_hachaton/reports/clustering/tfidf_clusters_comparison.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
    
    def compare_algorithms(self, results):
        """Сравнение алгоритмов кластеризации"""
        print("\nСравнение алгоритмов кластеризации:")
        print("=" * 50)
        
        comparison_data = []
        for algorithm, result in results.items():
            comparison_data.append({
                'Алгоритм': algorithm.upper(),
                'Количество кластеров': result['n_clusters'],
                'Silhouette Score': result['silhouette_score'],
                'Calinski-Harabasz Score': result['calinski_score'],
                'Davies-Bouldin Score': result['davies_bouldin_score']
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        print(comparison_df.to_string(index=False))
        
        # Визуализация сравнения
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        
        algorithms = list(results.keys())
        silhouette_scores = [results[alg]['silhouette_score'] for alg in algorithms]
        calinski_scores = [results[alg]['calinski_score'] for alg in algorithms]
        davies_bouldin_scores = [results[alg]['davies_bouldin_score'] for alg in algorithms]
        
        axes[0].bar(algorithms, silhouette_scores)
        axes[0].set_title('Silhouette Score (больше = лучше)')
        axes[0].set_ylabel('Score')
        
        axes[1].bar(algorithms, calinski_scores)
        axes[1].set_title('Calinski-Harabasz Score (больше = лучше)')
        axes[1].set_ylabel('Score')
        
        axes[2].bar(algorithms, davies_bouldin_scores)
        axes[2].set_title('Davies-Bouldin Score (меньше = лучше)')
        axes[2].set_ylabel('Score')
        
        plt.tight_layout()
        plt.savefig('/Users/mishantique/Desktop/Projects/gazprombank_hachaton/reports/clustering/tfidf_algorithms_comparison.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
        
        return comparison_df
    
    def save_results(self, results, output_path):
        """Сохранение результатов кластеризации"""
        print(f"Сохраняем результаты в {output_path}...")
        
        # Сохраняем DataFrame с результатами всех алгоритмов
        self.df.to_json(output_path, orient='records', indent=2)
        
        # Сохраняем подробный отчет
        summary_path = output_path.replace('.json', '_summary.txt')
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("РЕЗУЛЬТАТЫ TF-IDF КЛАСТЕРИЗАЦИИ\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Общее количество отзывов: {len(self.df)}\n")
            f.write(f"Размер TF-IDF матрицы: {self.tfidf_matrix.shape}\n\n")
            
            # Результаты по алгоритмам
            for algorithm, result in results.items():
                f.write(f"{algorithm.upper()} РЕЗУЛЬТАТЫ:\n")
                f.write("-" * 20 + "\n")
                f.write(f"Количество кластеров: {result['n_clusters']}\n")
                f.write(f"Silhouette Score: {result['silhouette_score']:.3f}\n")
                f.write(f"Calinski-Harabasz Score: {result['calinski_score']:.3f}\n")
                f.write(f"Davies-Bouldin Score: {result['davies_bouldin_score']:.3f}\n\n")
                
                # Детали по кластерам
                for cluster_info in result['cluster_analysis']:
                    f.write(f"{cluster_info['cluster_name']} ({cluster_info['size']} документов):\n")
                    f.write(f"  Основные продукты: {cluster_info['top_products']}\n")
                    f.write(f"  Ключевые слова: {', '.join([word for word, _ in cluster_info['top_words'][:5]])}\n")
                    f.write(f"  Средняя длина текста: {cluster_info['avg_length']:.0f} символов\n\n")
                
                f.write("\n")
        
        print("Результаты сохранены")

def main():
    """Основная функция"""
    # Путь к данным
    data_path = '/Users/mishantique/Desktop/Projects/gazprombank_hachaton/data/raw/sravni_ru/sravni_ru.json'
    
    # Создаем объект для кластеризации
    clustering = TfIdfClustering(data_path)
    
    # Выполняем кластеризацию
    clustering.load_data()
    clustering.prepare_texts()
    clustering.create_tfidf_matrix()
    
    # Выполняем кластеризацию разными алгоритмами
    results = clustering.perform_clustering(
        algorithms=['kmeans', 'agglomerative', 'dbscan']
    )
    
    # Анализируем и визуализируем результаты
    clustering.create_word_clouds(results)
    clustering.visualize_clusters(results)
    comparison_df = clustering.compare_algorithms(results)
    
    # Сохраняем результаты
    output_path = '/Users/mishantique/Desktop/Projects/gazprombank_hachaton/data/processed/tfidf_clustering_results.json'
    clustering.save_results(results, output_path)
    
    print("\nTF-IDF кластеризация завершена!")

if __name__ == "__main__":
    main()
