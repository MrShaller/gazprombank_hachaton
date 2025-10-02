#!/usr/bin/env python3
"""
Скрипт для автоматического запуска парсера с нужным URL
"""

from interactive_parser import InteractiveGazprombankParser

def main():
    url = "https://www.sravni.ru/bank/gazprombank/obsluzhivanie/otzyvy/?orderby=byDate"
    
    # Добавляем фильтр "Все" если его нет
    if 'filterby=all' not in url:
        separator = '&' if '?' in url else '?'
        url = f"{url}{separator}filterby=all"
        print(f"✅ Добавлен фильтр 'Все': {url}")
    
    parser = InteractiveGazprombankParser(headless=False)  # Обязательно видимый браузер
    
    try:
        print("\n✅ Ручная прокрутка + автоматический сбор + парсинг дат + рейтинги")
        print()
        
        # Парсинг всех отзывов
        reviews, filename = parser.parse_all_reviews(url)
        
        if reviews:
            # Сохранение результатов
            saved_path = parser.save_reviews(reviews, filename)
            
            # Статистика
            print(f"\n🎉 ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!")
            print(f"📊 Собрано {len(reviews)} отзывов")
            
            if reviews:
                lengths = [len(r['review_text']) for r in reviews]
                avg_length = sum(lengths) / len(lengths)
                
                # Анализ дат
                dates_found = len([r for r in reviews if r.get('review_date')])
                dates_percentage = (dates_found / len(reviews)) * 100
                
                # Анализ рейтингов
                ratings_found = len([r for r in reviews if r.get('rating') is not None])
                ratings_percentage = (ratings_found / len(reviews)) * 100
                
                # Распределение рейтингов
                rating_distribution = {}
                tonality_distribution = {}
                
                for review in reviews:
                    rating = review.get('rating')
                    tonality = review.get('tonality')
                    
                    if rating is not None:
                        rating_distribution[rating] = rating_distribution.get(rating, 0) + 1
                    
                    if tonality:
                        tonality_distribution[tonality] = tonality_distribution.get(tonality, 0) + 1
                
                print(f"\n📈 СТАТИСТИКА:")
                print(f"   📏 Средняя длина отзыва: {avg_length:.0f} символов")
                print(f"   📚 Самый длинный отзыв: {max(lengths)} символов")
                print(f"   📄 Самый короткий отзыв: {min(lengths)} символов")
                print(f"   📅 Найдено дат: {dates_found}/{len(reviews)} ({dates_percentage:.1f}%)")
                print(f"   ⭐ Найдено рейтингов: {ratings_found}/{len(reviews)} ({ratings_percentage:.1f}%)")
                
                # Показываем примеры найденных дат
                sample_dates = [r.get('review_date') for r in reviews[:5] if r.get('review_date')]
                if sample_dates:
                    print(f"   📅 Примеры дат: {', '.join(sample_dates[:3])}")
                
                # Распределение рейтингов
                if rating_distribution:
                    print(f"\n⭐ РАСПРЕДЕЛЕНИЕ РЕЙТИНГОВ:")
                    for rating in sorted(rating_distribution.keys()):
                        count = rating_distribution[rating]
                        percentage = (count / len(reviews)) * 100
                        print(f"   {rating} звёзд: {count} отзывов ({percentage:.1f}%)")
                
                # Распределение тональности
                if tonality_distribution:
                    print(f"\n😊 РАСПРЕДЕЛЕНИЕ ТОНАЛЬНОСТИ:")
                    for tonality in ['отрицательно', 'нейтрально', 'положительно']:
                        count = tonality_distribution.get(tonality, 0)
                        if count > 0:
                            percentage = (count / len(reviews)) * 100
                            print(f"   {tonality.capitalize()}: {count} отзывов ({percentage:.1f}%)")
            
            if saved_path:
                print(f"\n💾 Результаты сохранены в: {saved_path}")
        else:
            print("❌ Не удалось собрать отзывы")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        parser.close()

if __name__ == "__main__":
    main()

