#!/usr/bin/env python3
"""
Простой тест для проверки работы парсера
"""

import time
from webdriver_setup import setup_chrome_driver

def test_driver():
    try:
        print("🧪 Тестируем веб-драйвер...")
        driver = setup_chrome_driver(headless=False)
        
        print("✅ Драйвер создан, открываем тестовую страницу...")
        driver.get("https://www.google.com")
        time.sleep(3)
        
        title = driver.title
        print(f"📖 Заголовок страницы: {title}")
        
        driver.quit()
        print("✅ Драйвер успешно закрыт")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании драйвера: {e}")
        return False

if __name__ == "__main__":
    test_driver()

