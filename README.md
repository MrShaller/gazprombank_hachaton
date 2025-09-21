# 🏦 Bank Reviews Classifier

Проект по анализу отзывов клиентов банков:  
- Разделение текста на **клаузы** (аспектно-ориентированные сегменты).  
- Определение **тематики** отзыва (мультилейбл классификация).  
- Определение **сентимента** (положительный / нейтральный / отрицательный) по каждой теме.  

---

## 📂 Структура проекта
```
gazprombank_hachaton/
├── configs/ # Конфигурации проекта
│ ├── topics.yml # Список тем + синонимы (онтология)
│ ├── stopwords.txt # Основной список стоп-слов
│ └── stopwords_keep.txt # Слова, которые нельзя удалять (важны для тональности)
│
├── data/ # Данные
│ ├── raw/ # Сырые данные (выгрузки с парсера)
│ ├── interim/ # Промежуточные данные (разбитые на клаузы, очищенные)
│ └── processed/ # Финальные датасеты для обучения/инференса
│
├── reports/ # Результаты
│
│
├── scripts/ # Исходный код
│ ├── clause/
│ │ └── splitter.py - Сплиттер текста на клаузы 
│ ├── match_topics/ - 
│ │ ├── topic_matcher.py - # Функции: загрузка topics.yml для создания валидационного датасета
│ │ └── topic_matcher_all.py - Батч-скрипт: data/interim/clauses.csv → ..._with_topics.csv
│ ├── parsers/ - парсеры
│ │ ├── 
│ │ └──
│ ├── sentiments/ 
│ │ ├── sentiment_rules.py # Лексиконный скорер: POS/NEG слова/фразы, инверсия "не", усилители
│ │ └── sentiment_all.py # Батч-скрипт: ..._with_topics.csv → ..._sentiment.csv (70/30 смесь)
│ └── prepare_dataset.py - 
│  
│
├── tests/
│
├── 
│
└── 

```
---

## 🚀 Быстрый старт

1. Склонировать репозиторий:
   ```bash
   git clone https://github.com/MrShaller/gazprombank_hachaton
   cd gazprombank_hachaton

## Для себя:
   Чтобы вызвать python scripts/prepare_dataset.py -> нужно в data/raw/..... <<<< сюда поместить что-то

   Путь такой -> scripts/prepare_dataset.py (он вызывает clause/splitter.py)
                 scripts/match_topics/topic_matcher_all.py -> приписывает топики по правилам из topics.yml <- пока что работает плохо, это перед обучением модели + валидация
                 scripts/sentiments/sentiment_all.py -> приписывает тональность всем клаузам из interim по правилам в sentiment_rules.py <- тоже работает пока так себе