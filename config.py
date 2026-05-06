"""
Конфигурация проекта
"""

import os
from pathlib import Path

# OLLAMA 
OLLAMA_HOST = "http://26.206.215.215:11434"
OLLAMA_MODEL = "qwen3-vl:4b"  # Мультимодальная модель для чата и зрения
OLLAMA_CONNECT_TIMEOUT = 30  # Увеличено для удалённых туннелей (было 5)
OLLAMA_GENERATE_TIMEOUT = 120
OLLAMA_CHAT_TIMEOUT = 180
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "")  # Optional API key for Ollama Cloud

# ADB
ADB_PATH = "adb"  # Путь к ADB (предполагается в PATH)

# ПУТИ
PROJECT_ROOT = Path(__file__).parent
SCREENSHOT_DIR = PROJECT_ROOT / "screenshots"
LOGS_DIR = PROJECT_ROOT / "logs"

# Создать директории если не существуют
SCREENSHOT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ОТЛАДКА
DEBUG = True

# ФУНКЦИИ
def get_ollama_url():
    """Получить URL Ollama"""
    return OLLAMA_HOST

def get_model_name():
    """Получить имя модели"""
    return OLLAMA_MODEL

def validate_config():
    """Проверить конфигурацию"""
    print("\n" + "="*50)
    print("ПРОВЕРКА КОНФИГУРАЦИИ")
    print("="*50)
    print(f"Ollama: {OLLAMA_HOST}")
    print(f"Модель: {OLLAMA_MODEL}")
    print(f"Скриншоты: {SCREENSHOT_DIR}")
    print(f"ADB: {ADB_PATH}")
    print("="*50)
    return True

if __name__ == "__main__":
    validate_config()
