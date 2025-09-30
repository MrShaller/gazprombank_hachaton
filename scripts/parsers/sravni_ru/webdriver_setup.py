#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для автоматической настройки веб-драйвера
"""

import logging
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

def setup_firefox_driver(headless: bool = True) -> webdriver.Firefox:
    """
    Автоматическая настройка Firefox веб-драйвера
    
    Args:
        headless: Запуск в фоновом режиме
        
    Returns:
        Настроенный экземпляр Firefox WebDriver
    """
    try:
        # Настройки Firefox
        firefox_options = FirefoxOptions()
        
        if headless:
            firefox_options.add_argument("--headless")
        
        # Базовые настройки
        firefox_options.add_argument("--width=1920")
        firefox_options.add_argument("--height=1080")
        
        # Дополнительные настройки
        firefox_options.set_preference("dom.webdriver.enabled", False)
        firefox_options.set_preference("useAutomationExtension", False)
        
        # User agent для имитации обычного браузера
        user_agent = get_user_agent()
        firefox_options.set_preference("general.useragent.override", user_agent)
        
        # Используем системный geckodriver (установленный через brew)
        service = FirefoxService('/opt/homebrew/bin/geckodriver')
        
        # Создание драйвера
        driver = webdriver.Firefox(service=service, options=firefox_options)
        
        logger.info("Firefox веб-драйвер успешно настроен")
        return driver
        
    except Exception as e:
        logger.error(f"Ошибка при настройке Firefox веб-драйвера: {e}")
        raise

def setup_chrome_driver(headless: bool = True) -> webdriver.Chrome:
    """
    Автоматическая настройка Chrome веб-драйвера
    
    Args:
        headless: Запуск в фоновом режиме
        
    Returns:
        Настроенный экземпляр Chrome WebDriver
    """
    try:
        # Сначала пробуем Firefox как более стабильный вариант
        logger.info("Пытаемся использовать Firefox...")
        return setup_firefox_driver(headless)
    except Exception as e:
        logger.warning(f"Firefox не доступен: {e}. Пробуем Chrome...")
        
    try:
        # Настройки Chrome
        chrome_options = ChromeOptions()
        
        if headless:
            chrome_options.add_argument("--headless")
        
        # Базовые настройки
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent для имитации обычного браузера
        user_agent = get_user_agent()
        chrome_options.add_argument(f"--user-agent={user_agent}")
        
        # Используем системный chromedriver (установленный через brew)
        service = ChromeService('/opt/homebrew/bin/chromedriver')
        
        # Создание драйвера
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Дополнительные настройки для обхода детекции автоматизации
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logger.info("Chrome веб-драйвер успешно настроен")
        return driver
        
    except Exception as e:
        logger.error(f"Ошибка при настройке Chrome веб-драйвера: {e}")
        raise

def get_user_agent() -> str:
    """Возвращает подходящий User-Agent в зависимости от ОС"""
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    elif system == "windows":
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    else:  # Linux
        return "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
