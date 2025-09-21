#!/usr/bin/env python3
"""
Универсальный интерактивный парсер отзывов Газпромбанка с Sravni.ru
Пользователь прокручивает страницу вручную, затем парсер собирает все отзывы с датами
"""

import json
import time
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from webdriver_setup import setup_chrome_driver

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InteractiveGazprombankParser:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        self.data_dir = Path("data/sravni_ru")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _setup_driver(self):
        """Настройка веб-драйвера"""
        self.driver = setup_chrome_driver(headless=self.headless)
        logger.info("Веб-драйвер успешно инициализирован")

    def _extract_product_info(self, url: str) -> tuple[str, str]:
        """Извлекает информацию о продукте из URL"""
        # Словарь соответствий URL-путей и названий продуктов
        product_mapping = {
            'avtokredity': ('Автокредиты', 'avtokredity'),
            'debetovye-karty': ('Дебетовые карты', 'debetovye_karty'),
            'kreditnye-karty': ('Кредитные карты', 'kreditnye_karty'), 
            'karty': ('Кредитные карты', 'kreditnye_karty'),
            'kredity': ('Кредиты наличными', 'kredity'),
            'vklady': ('Вклады', 'vklady'),
            'ipoteka': ('Ипотека', 'ipoteka'),
            'refinansirovanie-kreditov': ('Рефинансирование кредитов', 'refinansirovanie_kreditov'),
            'refinansirovanie-ipoteki': ('Рефинансирование ипотеки', 'refinansirovanie_ipoteki'),
            'obsluzhivanie': ('Обслуживание', 'obsluzhivanie'),
            'distancionnoe-obsluzhivanie': ('Дистанционное обслуживание', 'distancionnoe_obsluzhivanie'),
            'mobile-app': ('Мобильное приложение', 'mobile_app'),
            'exchange': ('Обмен валют', 'exchange'),
            'other-service': ('Прочие услуги', 'other_service'),
            'acquiring': ('Acquiring', 'acquiring'),
            'rko': ('RKO', 'rko'),
            'remittance': ('Remittance', 'remittance'),
            'conditions': ('Conditions', 'conditions')
        }
        
        # Извлекаем путь из URL
        parsed = urlparse(url)
        path_parts = [part for part in parsed.path.split('/') if part]
        
        # Ищем соответствующий продукт в пути
        for part in path_parts:
            if part in product_mapping:
                return product_mapping[part]
        
        # Если не найдено, пытаемся определить по последней части пути
        if len(path_parts) >= 2:
            potential_product = path_parts[-2]  # Берем часть перед 'otzyvy'
            clean_product = potential_product.replace('-', '_')
            product_name = potential_product.replace('-', ' ').title()
            return (product_name, clean_product)
        
        # Fallback
        return ('Неизвестный продукт', 'unknown_product')

    def wait_for_manual_scroll(self, main_url: str) -> List[str]:
        """Ожидает ручной прокрутки пользователем, затем собирает URL отзывов"""
        self._setup_driver()
        
        logger.info(f"Загружаем страницу: {main_url}")
        self.driver.get(main_url)
        time.sleep(3)
        
        # Определяем продукт для отображения
        product_name, _ = self._extract_product_info(main_url)
        
        print("\n" + "="*80)
        print(f"🎮 ИНТЕРАКТИВНЫЙ РЕЖИМ ПАРСИНГА: {product_name.upper()}")
        print("="*80)
        print("📋 ИНСТРУКЦИЯ:")
        print("   1. Браузер открыт и готов к работе")
        print("   2. Прокрутите страницу ВРУЧНУЮ до самого конца")
        print("   3. Убедитесь, что все отзывы загружены")
        print("   4. Когда закончите прокрутку, НЕ ТРОГАЙТЕ браузер 5 секунд")
        print("   5. Парсер автоматически начнет сбор URL отзывов")
        print()
        print("⚠️  ВАЖНО:")
        print("   - НЕ закрывайте браузер")
        print("   - НЕ переходите на другие вкладки")
        print("   - Прокручивайте медленно для полной загрузки")
        print("="*80)
        
        # Мониторинг активности прокрутки
        last_scroll_time = time.time()
        last_height = 0
        stable_count = 0
        max_stable_time = 5  # 5 секунд бездействия
        
        print("🔄 Ожидаем ручную прокрутку...")
        print("💡 Совет: прокручивайте медленно, давая время на загрузку новых отзывов")
        
        while True:
            current_time = time.time()
            current_height = self.driver.execute_script("return window.pageYOffset")
            
            # Проверяем, изменилась ли позиция прокрутки
            if current_height != last_height:
                last_scroll_time = current_time
                last_height = current_height
                stable_count = 0
                print(f"📍 Прокрутка обнаружена, позиция: {current_height}")
            else:
                # Считаем время бездействия
                idle_time = current_time - last_scroll_time
                if idle_time >= max_stable_time:
                    print(f"\n✅ Бездействие {idle_time:.1f} сек - начинаем сбор URL!")
                    break
                else:
                    # Показываем обратный отсчет
                    remaining = max_stable_time - idle_time
                    print(f"⏳ Ожидание завершения прокрутки: {remaining:.1f} сек", end="\r")
            
            time.sleep(0.5)  # Проверяем каждые 0.5 секунд
        
        print("\n🔍 НАЧИНАЕМ СБОР URL ОТЗЫВОВ...")
        
        # Собираем все URL отзывов
        review_links = []
        unique_review_ids = set()
        
        selectors = [
            "a[href*='/otzyvy/'][href*='/']",
            "a[class*='review'][href*='/']", 
            "a[href*='/bank/gazprombank/otzyvy/']"
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                logger.info(f"Найдено {len(elements)} элементов с селектором: {selector}")
                
                for element in elements:
                    href = element.get_attribute('href')
                    if href and '/otzyvy/' in href:
                        # Очищаем URL от якорей
                        clean_url = href.split('#')[0]
                        if clean_url.endswith('/'):
                            clean_url = clean_url[:-1]
                        
                        # Проверяем, что это отзыв с числовым ID
                        url_parts = clean_url.split('/')
                        if len(url_parts) >= 2 and url_parts[-1].isdigit():
                            review_id = url_parts[-1]
                            
                            # Добавляем только уникальные отзывы
                            if review_id not in unique_review_ids:
                                unique_review_ids.add(review_id)
                                review_links.append(clean_url + '/')
                                
            except Exception as e:
                logger.warning(f"Ошибка при поиске с селектором {selector}: {e}")
                continue
        
        logger.info(f"🎉 Собрано {len(review_links)} уникальных URL отзывов")
        
        # Показываем статистику
        print(f"\n📊 РЕЗУЛЬТАТЫ СБОРА URL:")
        print(f"   🔗 Найдено уникальных URL: {len(review_links)}")
        
        return review_links

    def _parse_date(self, date_text: str) -> Optional[str]:
        """Парсит дату из текста и приводит к стандартному формату"""
        if not date_text:
            return None
            
        try:
            # Убираем лишние пробелы
            date_text = date_text.strip()
            
            # Словарь для замены месяцев на русском
            months_ru = {
                'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04',
                'мая': '05', 'июня': '06', 'июля': '07', 'августа': '08',
                'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12'
            }
            
            # Паттерн для даты вида "23 августа 2024"
            pattern = r'(\d{1,2})\s+([а-я]+)\s+(\d{4})'
            match = re.search(pattern, date_text.lower())
            
            if match:
                day, month_name, year = match.groups()
                if month_name in months_ru:
                    month = months_ru[month_name]
                    # Форматируем в ISO формат
                    formatted_date = f"{year}-{month}-{day.zfill(2)}"
                    return formatted_date
            
            # Если не удалось распарсить, возвращаем исходный текст
            return date_text
            
        except Exception as e:
            logger.warning(f"Ошибка парсинга даты '{date_text}': {e}")
            return date_text

    def parse_single_review(self, review_url: str, product_name: str) -> Optional[Dict[str, str]]:
        """Парсит один отзыв по URL с извлечением даты"""
        try:
            logger.info(f"Парсим отзыв: {review_url}")
            self.driver.get(review_url)
            time.sleep(2)
            
            # Проверяем, что мы на правильной странице
            current_url = self.driver.current_url
            if review_url not in current_url and not current_url.endswith(review_url.split('/')[-2] + '/'):
                logger.warning(f"Неожиданный URL: ожидался {review_url}, получен {current_url}")
                return None
            
            # Ищем текст отзыва
            text_selectors = [
                "div[class*='review-card_text__']",
                "div[class*='review-text']", 
                "div[class*='content']",
                "article",
                "main",
                "section"
            ]
            
            # Ищем дату отзыва
            date_selectors = [
                "div[class*='h-color-D30__1aja02n__1w661f']",  # Основной селектор
                "div[class*='h-color-D30']",
                "div[class*='1aja02n']",
                "div[class*='1w661f']",
                "span[class*='date']",
                "time",
                "[datetime]"
            ]
            
            full_text = None
            review_date = None
            
            # Парсим текст отзыва
            for selector in text_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        # Берем только первый элемент
                        elem = elements[0]
                        text = elem.text.strip()
                        
                        if len(text) > 100:
                            if not any(pattern in text.lower() for pattern in [
                                'навигация', 'меню', 'войти', 'регистрация',
                                'подбор кредита', 'сравни в мобильном', 'к списку отзывов',
                                'другие отзывы', 'оставьте отзыв', 'рейтинг банков', 'комментарий'
                            ]):
                                full_text = text
                                logger.info(f"Найден основной отзыв с селектором {selector}: {len(text)} символов")
                                break
                except Exception:
                    continue
            
            # Парсим дату отзыва
            for selector in date_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        for elem in elements:
                            date_text = elem.text.strip()
                            # Проверяем, что это похоже на дату
                            if date_text and (
                                re.search(r'\d{1,2}\s+[а-я]+\s+\d{4}', date_text.lower()) or  # "23 августа 2024"
                                re.search(r'\d{1,2}\.\d{1,2}\.\d{4}', date_text) or  # "23.08.2024"
                                any(month in date_text.lower() for month in [
                                    'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                                    'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
                                ])
                            ):
                                review_date = self._parse_date(date_text)
                                logger.info(f"Найдена дата отзыва с селектором {selector}: {date_text} -> {review_date}")
                                break
                    if review_date:
                        break
                except Exception:
                    continue
            
            if full_text:
                # Минимальная очистка текста
                cleaned_text = ' '.join(full_text.split())
                
                if len(cleaned_text) > 50:
                    # Извлекаем ID отзыва из URL
                    review_id = review_url.rstrip('/').split('/')[-1]
                    
                    review_data = {
                        "review_id": review_id,
                        "review_text": cleaned_text,
                        "review_date": review_date,  # Добавляем дату
                        "url": review_url,
                        "parsed_at": datetime.now().isoformat(),
                        "bank_name": "gazprombank",
                        "product_type": product_name
                    }
                    
                    logger.info(f"Успешно извлечен отзыв длиной {len(cleaned_text)} символов с датой {review_date} с URL {review_url}")
                    return review_data
                else:
                    logger.warning(f"Текст отзыва слишком короткий ({len(cleaned_text)} символов)")
            
            logger.warning(f"Не удалось извлечь текст отзыва с URL: {review_url}")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге отзыва {review_url}: {e}")
            return None

    def parse_all_reviews(self, main_url: str) -> List[Dict]:
        """Парсит все отзывы со страницы"""
        # Определяем информацию о продукте
        product_name, filename_base = self._extract_product_info(main_url)
        
        # Этап 1: Ручная прокрутка и сбор URL
        print("🔄 ЭТАП 1: СБОР URL ОТЗЫВОВ")
        review_urls = self.wait_for_manual_scroll(main_url)
        
        if not review_urls:
            print("❌ Не найдено URL отзывов")
            return []
        
        # Этап 2: Парсинг каждого отзыва
        print(f"\n🔄 ЭТАП 2: ПАРСИНГ {len(review_urls)} ОТЗЫВОВ")
        all_reviews = []
        
        for i, review_url in enumerate(review_urls, 1):
            print(f"📝 Обрабатываем отзыв {i}/{len(review_urls)}")
            
            review_data = self.parse_single_review(review_url, product_name)
            if review_data:
                review_data["review_id"] = str(i)  # Перенумеровываем
                all_reviews.append(review_data)
            
            # Пауза между запросами
            time.sleep(1)
        
        return all_reviews, filename_base

    def save_reviews(self, reviews: List[Dict], filename: str):
        """Сохраняет отзывы в JSON файл"""
        if not reviews:
            logger.warning("Нет отзывов для сохранения")
            return
        
        json_path = self.data_dir / f"{filename}.json"
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(reviews, f, ensure_ascii=False, indent=2)
            logger.info(f"Отзывы сохранены в JSON: {json_path}")
            return json_path
        except Exception as e:
            logger.error(f"Ошибка при сохранении JSON: {e}")
            return None

    def close(self):
        """Закрывает веб-драйвер"""
        if self.driver:
            self.driver.quit()
            logger.info("Веб-драйвер закрыт")

def main():
    """Основная функция для запуска парсера"""
    print("🚀 УНИВЕРСАЛЬНЫЙ ИНТЕРАКТИВНЫЙ ПАРСЕР ГАЗПРОМБАНКА")
    print("="*60)
    print()
    
    # Запрашиваем URL у пользователя
    url = input("📝 Введите URL страницы отзывов: ").strip()
    
    if not url:
        print("❌ URL не может быть пустым!")
        return
    
    if 'gazprombank' not in url or 'otzyvy' not in url:
        print("❌ URL должен содержать отзывы Газпромбанка с сайта Sravni.ru")
        return
    
    # Добавляем фильтр "Все" если его нет
    if 'filterby=all' not in url:
        separator = '&' if '?' in url else '?'
        url = f"{url}{separator}filterby=all"
        print(f"✅ Добавлен фильтр 'Все': {url}")
    
    parser = InteractiveGazprombankParser(headless=False)  # Обязательно видимый браузер
    
    try:
        print("\n✅ Ручная прокрутка + автоматический сбор + парсинг дат")
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
                
                print(f"\n📈 СТАТИСТИКА:")
                print(f"   📏 Средняя длина отзыва: {avg_length:.0f} символов")
                print(f"   📚 Самый длинный отзыв: {max(lengths)} символов")
                print(f"   📄 Самый короткий отзыв: {min(lengths)} символов")
                print(f"   📅 Найдено дат: {dates_found}/{len(reviews)} ({dates_percentage:.1f}%)")
                
                # Показываем примеры найденных дат
                sample_dates = [r.get('review_date') for r in reviews[:5] if r.get('review_date')]
                if sample_dates:
                    print(f"   📅 Примеры дат: {', '.join(sample_dates[:3])}")
            
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
