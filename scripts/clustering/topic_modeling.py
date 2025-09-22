#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тематическое моделирование отзывов с использованием LDA и BERTopic

Этот скрипт выполняет тематическое моделирование текстов отзывов 
для выявления скрытых тематических структур.
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

# Для LDA
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import pyLDAvis
import pyLDAvis.lda_model

# Для BERTopic
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN

# Для предобработки текста
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer
import pymorphy2

class TopicModeling:
    def __init__(self, data_path):
        """
        Инициализация класса для тематического моделирования
        
        Args:
            data_path (str): Путь к JSON файлу с данными
        """
        self.data_path = data_path
        self.data = None
        self.df = None
        self.processed_texts = None
        self.morph = pymorphy2.MorphAnalyzer()
        
        # Загружаем стоп-слова
        try:
            self.stop_words = set(stopwords.words('russian'))
        except LookupError:
            nltk.download('stopwords')
            nltk.download('punkt')
            self.stop_words = set(stopwords.words('russian'))
        
        # Добавляем банковские стоп-слова
        banking_stopwords = {
            'банк', 'банка', 'банке', 'банком', 'банки', 'банков', 'банкам', 'банками',
            'газпромбанк', 'газпром', 'гпб', 'отзыв', 'отзыва', 'отзывы', 'отзывов',
            'клиент', 'клиента', 'клиенты', 'клиентов', 'сервис', 'услуга', 'услуги',
            'год', 'года', 'лет', 'месяц', 'месяца', 'месяцев', 'день', 'дня', 'дней',
            'рубль', 'рубля', 'рублей', 'тысяча', 'тысяч', 'миллион', 'миллионов'
        }
        self.stop_words.update(banking_stopwords)
        
    def load_data(self):
        """Загрузка данных из JSON файла"""
        print("Загружаем данные...")
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        self.df = pd.DataFrame(self.data)
        print(f"Загружено {len(self.df)} отзывов")
        
    def preprocess_text(self, text):
        """
        Глубокая предобработка текста для тематического моделирования
        
        Args:
            text (str): Исходный текст
            
        Returns:
            str: Обработанный текст
        """
        if not text:
            return ""
        
        # Приводим к нижнему регистру
        text = text.lower()
        
        # Убираем специальные символы и цифры
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
    
    def lda_modeling(self, n_topics_range=(5, 25)):
        """
        Тематическое моделирование с использованием LDA
        
        Args:
            n_topics_range (tuple): Диапазон количества тем для тестирования
            
        Returns:
            dict: Результаты LDA моделирования
        """
        print("Выполняем LDA моделирование...")
        
        # Векторизация текстов
        vectorizer = CountVectorizer(
            max_features=1000,
            min_df=5,
            max_df=0.8,
            ngram_range=(1, 2)
        )
        
        doc_term_matrix = vectorizer.fit_transform(self.processed_texts)
        feature_names = vectorizer.get_feature_names_out()
        
        # Поиск оптимального количества тем
        print("Ищем оптимальное количество тем...")
        perplexities = []
        log_likelihoods = []
        
        min_topics, max_topics = n_topics_range
        topics_range = range(min_topics, max_topics + 1, 2)
        
        best_model = None
        best_perplexity = float('inf')
        
        for n_topics in topics_range:
            lda_model = LatentDirichletAllocation(
                n_components=n_topics,
                random_state=42,
                max_iter=100,
                learning_method='batch'
            )
            lda_model.fit(doc_term_matrix)
            
            perplexity = lda_model.perplexity(doc_term_matrix)
            log_likelihood = lda_model.score(doc_term_matrix)
            
            perplexities.append(perplexity)
            log_likelihoods.append(log_likelihood)
            
            if perplexity < best_perplexity:
                best_perplexity = perplexity
                best_model = lda_model
            
            print(f"  {n_topics} тем: perplexity = {perplexity:.2f}, log-likelihood = {log_likelihood:.2f}")
        
        # Визуализация метрик
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        ax1.plot(topics_range, perplexities, 'bo-')
        ax1.set_xlabel('Количество тем')
        ax1.set_ylabel('Perplexity')
        ax1.set_title('Perplexity vs Количество тем')
        ax1.grid(True)
        
        ax2.plot(topics_range, log_likelihoods, 'ro-')
        ax2.set_xlabel('Количество тем')
        ax2.set_ylabel('Log Likelihood')
        ax2.set_title('Log Likelihood vs Количество тем')
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig('/Users/mishantique/Desktop/Projects/gazprombank_hachaton/reports/clustering/lda_optimization.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
        
        # Анализ лучшей модели
        optimal_topics = best_model.n_components
        print(f"\nОптимальное количество тем: {optimal_topics}")
        
        # Получаем распределения тем по документам
        doc_topic_probs = best_model.transform(doc_term_matrix)
        
        # Присваиваем каждому документу доминирующую тему
        dominant_topics = np.argmax(doc_topic_probs, axis=1)
        self.df['lda_topic'] = dominant_topics
        
        # Анализируем темы
        lda_results = self._analyze_lda_topics(best_model, feature_names, doc_topic_probs)
        
        # Создаем интерактивную визуализацию (если возможно)
        try:
            vis = pyLDAvis.lda_model.prepare(best_model, doc_term_matrix, vectorizer)
            pyLDAvis.save_html(vis, '/Users/mishantique/Desktop/Projects/gazprombank_hachaton/reports/clustering/lda_visualization.html')
            print("Интерактивная визуализация сохранена в reports/lda_visualization.html")
        except Exception as e:
            print(f"Не удалось создать интерактивную визуализацию: {e}")
        
        return lda_results
    
    def _analyze_lda_topics(self, model, feature_names, doc_topic_probs):
        """Анализ тем LDA модели"""
        print("\nАнализ тем LDA:")
        print("=" * 50)
        
        topics_info = []
        
        for topic_idx, topic in enumerate(model.components_):
            # Топ слова темы
            top_words_idx = topic.argsort()[-10:][::-1]
            top_words = [feature_names[i] for i in top_words_idx]
            top_weights = [topic[i] for i in top_words_idx]
            
            # Документы, относящиеся к этой теме
            topic_docs = self.df[self.df['lda_topic'] == topic_idx]
            
            # Наиболее частые типы продуктов в теме
            if len(topic_docs) > 0:
                top_products = topic_docs['product_type'].value_counts().head(3)
                avg_confidence = doc_topic_probs[self.df['lda_topic'] == topic_idx, topic_idx].mean()
            else:
                top_products = pd.Series(dtype=int)
                avg_confidence = 0
            
            topic_info = {
                'topic_id': topic_idx,
                'size': len(topic_docs),
                'top_words': list(zip(top_words, top_weights)),
                'top_products': top_products.to_dict() if len(top_products) > 0 else {},
                'avg_confidence': avg_confidence
            }
            topics_info.append(topic_info)
            
            print(f"\nТема {topic_idx} ({len(topic_docs)} документов, уверенность: {avg_confidence:.3f}):")
            print(f"  Ключевые слова: {', '.join(top_words[:5])}")
            if len(top_products) > 0:
                print(f"  Основные продукты: {dict(top_products)}")
        
        return {
            'model': model,
            'topics_info': topics_info,
            'doc_topic_probs': doc_topic_probs
        }
    
    def bertopic_modeling(self):
        """
        Тематическое моделирование с использованием BERTopic
        
        Returns:
            dict: Результаты BERTopic моделирования
        """
        print("Выполняем BERTopic моделирование...")
        
        # Настройка компонентов BERTopic
        sentence_model = SentenceTransformer('cointegrated/rubert-tiny2')
        
        umap_model = UMAP(
            n_neighbors=15,
            n_components=5,
            min_dist=0.0,
            metric='cosine',
            random_state=42
        )
        
        hdbscan_model = HDBSCAN(
            min_cluster_size=15,
            metric='euclidean',
            cluster_selection_method='eom'
        )
        
        # Создаем BERTopic модель
        topic_model = BERTopic(
            embedding_model=sentence_model,
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            vectorizer_model=CountVectorizer(
                ngram_range=(1, 2),
                stop_words=list(self.stop_words),
                min_df=5,
                max_df=0.8
            ),
            language='russian',
            verbose=True
        )
        
        # Обучаем модель
        topics, probs = topic_model.fit_transform(self.processed_texts)
        
        # Добавляем результаты в DataFrame
        self.df['bertopic_topic'] = topics
        self.df['bertopic_prob'] = probs
        
        # Анализируем результаты
        bertopic_results = self._analyze_bertopic_topics(topic_model, topics, probs)
        
        # Создаем визуализации
        self._create_bertopic_visualizations(topic_model)
        
        return bertopic_results
    
    def _analyze_bertopic_topics(self, model, topics, probs):
        """Анализ тем BERTopic модели"""
        print("\nАнализ тем BERTopic:")
        print("=" * 50)
        
        topic_info = model.get_topic_info()
        topics_info = []
        
        for _, row in topic_info.iterrows():
            topic_id = row['Topic']
            
            if topic_id == -1:  # Outlier topic
                continue
                
            # Получаем информацию о теме
            topic_words = model.get_topic(topic_id)
            topic_docs = self.df[self.df['bertopic_topic'] == topic_id]
            
            # Наиболее частые типы продуктов в теме
            if len(topic_docs) > 0:
                top_products = topic_docs['product_type'].value_counts().head(3)
                avg_confidence = topic_docs['bertopic_prob'].mean()
            else:
                top_products = pd.Series(dtype=int)
                avg_confidence = 0
            
            topic_info_dict = {
                'topic_id': topic_id,
                'size': len(topic_docs),
                'top_words': topic_words,
                'top_products': top_products.to_dict() if len(top_products) > 0 else {},
                'avg_confidence': avg_confidence
            }
            topics_info.append(topic_info_dict)
            
            print(f"\nТема {topic_id} ({len(topic_docs)} документов, уверенность: {avg_confidence:.3f}):")
            print(f"  Ключевые слова: {', '.join([word for word, _ in topic_words[:5]])}")
            if len(top_products) > 0:
                print(f"  Основные продукты: {dict(top_products)}")
        
        return {
            'model': model,
            'topics_info': topics_info,
            'topic_info_df': topic_info
        }
    
    def _create_bertopic_visualizations(self, model):
        """Создание визуализаций для BERTopic"""
        print("Создаем визуализации BERTopic...")
        
        try:
            # Визуализация тем
            fig1 = model.visualize_topics()
            fig1.write_html('/Users/mishantique/Desktop/Projects/gazprombank_hachaton/reports/clustering/bertopic_topics.html')
            
            # Визуализация иерархии тем
            fig2 = model.visualize_hierarchy()
            fig2.write_html('/Users/mishantique/Desktop/Projects/gazprombank_hachaton/reports/clustering/bertopic_hierarchy.html')
            
            # Heatmap тем
            fig3 = model.visualize_heatmap()
            fig3.write_html('/Users/mishantique/Desktop/Projects/gazprombank_hachaton/reports/clustering/bertopic_heatmap.html')
            
            print("Визуализации BERTopic сохранены в папке reports/")
            
        except Exception as e:
            print(f"Ошибка при создании визуализаций: {e}")
    
    def compare_methods(self, lda_results, bertopic_results):
        """Сравнение результатов LDA и BERTopic"""
        print("\nСравнение методов:")
        print("=" * 50)
        
        # Статистика по методам
        lda_topics = len(lda_results['topics_info'])
        bertopic_topics = len([t for t in bertopic_results['topics_info'] if t['topic_id'] != -1])
        
        lda_outliers = len(self.df[self.df['lda_topic'] == -1]) if -1 in self.df['lda_topic'].values else 0
        bertopic_outliers = len(self.df[self.df['bertopic_topic'] == -1])
        
        print(f"LDA:")
        print(f"  Количество тем: {lda_topics}")
        print(f"  Outliers: {lda_outliers}")
        
        print(f"\nBERTopic:")
        print(f"  Количество тем: {bertopic_topics}")
        print(f"  Outliers: {bertopic_outliers}")
        
        # Создаем сравнительную визуализацию
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Распределение размеров кластеров LDA
        lda_sizes = [info['size'] for info in lda_results['topics_info']]
        ax1.bar(range(len(lda_sizes)), lda_sizes)
        ax1.set_title('Размеры тем - LDA')
        ax1.set_xlabel('ID темы')
        ax1.set_ylabel('Количество документов')
        
        # Распределение размеров кластеров BERTopic
        bertopic_sizes = [info['size'] for info in bertopic_results['topics_info'] if info['topic_id'] != -1]
        ax2.bar(range(len(bertopic_sizes)), bertopic_sizes)
        ax2.set_title('Размеры тем - BERTopic')
        ax2.set_xlabel('ID темы')
        ax2.set_ylabel('Количество документов')
        
        # Распределение уверенности LDA
        if 'avg_confidence' in lda_results['topics_info'][0]:
            lda_confidences = [info['avg_confidence'] for info in lda_results['topics_info']]
            ax3.hist(lda_confidences, bins=20, alpha=0.7)
            ax3.set_title('Распределение уверенности - LDA')
            ax3.set_xlabel('Уверенность')
            ax3.set_ylabel('Частота')
        
        # Распределение уверенности BERTopic
        bertopic_confidences = [info['avg_confidence'] for info in bertopic_results['topics_info'] if info['topic_id'] != -1]
        ax4.hist(bertopic_confidences, bins=20, alpha=0.7)
        ax4.set_title('Распределение уверенности - BERTopic')
        ax4.set_xlabel('Уверенность')
        ax4.set_ylabel('Частота')
        
        plt.tight_layout()
        plt.savefig('/Users/mishantique/Desktop/Projects/gazprombank_hachaton/reports/clustering/topic_modeling_comparison.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
    
    def save_results(self, lda_results, bertopic_results, output_path):
        """Сохранение результатов тематического моделирования"""
        print(f"Сохраняем результаты в {output_path}...")
        
        # Сохраняем DataFrame с результатами
        self.df.to_json(output_path, orient='records', indent=2)
        
        # Сохраняем подробный отчет
        summary_path = output_path.replace('.json', '_summary.txt')
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("РЕЗУЛЬТАТЫ ТЕМАТИЧЕСКОГО МОДЕЛИРОВАНИЯ\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Общее количество отзывов: {len(self.df)}\n\n")
            
            # LDA результаты
            f.write("LDA РЕЗУЛЬТАТЫ:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Количество тем: {len(lda_results['topics_info'])}\n\n")
            
            for topic_info in lda_results['topics_info']:
                f.write(f"Тема {topic_info['topic_id']} ({topic_info['size']} документов):\n")
                f.write(f"  Ключевые слова: {', '.join([word for word, _ in topic_info['top_words'][:5]])}\n")
                if topic_info['top_products']:
                    f.write(f"  Основные продукты: {topic_info['top_products']}\n")
                f.write(f"  Средняя уверенность: {topic_info['avg_confidence']:.3f}\n\n")
            
            # BERTopic результаты
            f.write("\nBERTOPIC РЕЗУЛЬТАТЫ:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Количество тем: {len([t for t in bertopic_results['topics_info'] if t['topic_id'] != -1])}\n\n")
            
            for topic_info in bertopic_results['topics_info']:
                if topic_info['topic_id'] != -1:
                    f.write(f"Тема {topic_info['topic_id']} ({topic_info['size']} документов):\n")
                    f.write(f"  Ключевые слова: {', '.join([word for word, _ in topic_info['top_words'][:5]])}\n")
                    if topic_info['top_products']:
                        f.write(f"  Основные продукты: {topic_info['top_products']}\n")
                    f.write(f"  Средняя уверенность: {topic_info['avg_confidence']:.3f}\n\n")
        
        print("Результаты сохранены")

def main():
    """Основная функция"""
    # Путь к данным
    data_path = '/Users/mishantique/Desktop/Projects/gazprombank_hachaton/data/raw/sravni_ru/sravni_ru.json'
    
    # Создаем объект для тематического моделирования
    topic_modeling = TopicModeling(data_path)
    
    # Выполняем моделирование
    topic_modeling.load_data()
    topic_modeling.prepare_texts()
    
    # LDA моделирование
    lda_results = topic_modeling.lda_modeling()
    
    # BERTopic моделирование
    bertopic_results = topic_modeling.bertopic_modeling()
    
    # Сравниваем методы
    topic_modeling.compare_methods(lda_results, bertopic_results)
    
    # Сохраняем результаты
    output_path = '/Users/mishantique/Desktop/Projects/gazprombank_hachaton/data/processed/topic_modeling_results.json'
    topic_modeling.save_results(lda_results, bertopic_results, output_path)
    
    print("\nТематическое моделирование завершено!")

if __name__ == "__main__":
    main()
