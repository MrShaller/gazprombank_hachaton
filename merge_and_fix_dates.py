#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
from datetime import datetime
from pathlib import Path

def russian_month_to_number(month_name):
    """Преобразует русское название месяца в номер"""
    months = {
        'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04',
        'мая': '05', 'июня': '06', 'июля': '07', 'августа': '08',
        'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12'
    }
    return months.get(month_name.lower(), '01')

def fix_date_format(date_str):
    """Исправляет формат даты с 'день месяц' на 'YYYY-MM-DD'"""
    if not date_str or date_str == 'N/A':
        return date_str
    
    # Если дата уже в правильном формате YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    
    # Обрабатываем формат "день месяц" (например, "5 сентября", "26 августа")
    pattern = r'^(\d{1,2})\s+(\w+)$'
    match = re.match(pattern, date_str.strip())
    
    if match:
        day = match.group(1).zfill(2)
        month_name = match.group(2)
        month = russian_month_to_number(month_name)
        year = '2025'  # Текущий год для дат без года
        
        return f"{year}-{month}-{day}"
    
    return date_str

def merge_json_files():
    """Объединяет все JSON файлы в один с уникальными ID и исправленными датами"""
    
    data_dir = Path("data/raw/sravni_ru")
    output_file = data_dir / "sravni_ru.json"
    
    all_reviews = []
    current_id = 1
    files_processed = 0
    total_reviews = 0
    dates_fixed = 0
    
    print("🔄 ОБЪЕДИНЕНИЕ ФАЙЛОВ И ИСПРАВЛЕНИЕ ДАТ")
    print("=" * 50)
    
    # Обрабатываем все JSON файлы в папке
    for json_file in sorted(data_dir.glob("*.json")):
        if json_file.name == "sravni_ru.json":
            continue  # Пропускаем выходной файл
            
        print(f"📄 Обрабатываем: {json_file.name}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_reviews = 0
            file_dates_fixed = 0
            
            for review in data:
                # Присваиваем новый уникальный ID
                review['review_id'] = str(current_id)
                current_id += 1
                
                # Исправляем формат даты
                if 'review_date' in review:
                    original_date = review['review_date']
                    fixed_date = fix_date_format(original_date)
                    
                    if original_date != fixed_date:
                        review['review_date'] = fixed_date
                        file_dates_fixed += 1
                
                all_reviews.append(review)
                file_reviews += 1
            
            print(f"   ✅ {file_reviews} отзывов, {file_dates_fixed} дат исправлено")
            
            files_processed += 1
            total_reviews += file_reviews
            dates_fixed += file_dates_fixed
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    # Сохраняем объединенный файл
    print(f"\n💾 Сохраняем объединенный файл...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_reviews, f, ensure_ascii=False, indent=2)
    
    # Статистика
    print("\n📊 ИТОГОВАЯ СТАТИСТИКА:")
    print("=" * 50)
    print(f"📁 Обработано файлов: {files_processed}")
    print(f"📝 Всего отзывов: {total_reviews}")
    print(f"🔄 ID переназначено: {total_reviews}")
    print(f"📅 Дат исправлено: {dates_fixed}")
    print(f"💾 Размер файла: {output_file.stat().st_size / (1024*1024):.2f} MB")
    print(f"📍 Файл сохранен: {output_file}")
    
    return total_reviews, dates_fixed

if __name__ == "__main__":
    merge_json_files()
