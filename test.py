#!/usr/bin/env python3
"""
Быстрый тест основных компонентов PhoneDriverPP
"""

import sys
from pathlib import Path

def test_imports():
    """Проверить что все импорты работают"""
    print("=" * 60)
    print("🧪 ТЕСТ ИМПОРТОВ")
    print("=" * 60)
    
    try:
        print("Импортируем config...", end=" ")
        from config import OLLAMA_HOST, OLLAMA_MODEL, DEBUG
        print("✅")
        
        print("Импортируем executor...", end=" ")
        from executor import Executor
        print("✅")
        
        print("Импортируем vision...", end=" ")
        from vision import VisionAnalyzer
        print("✅")
        
        print("Импортируем task_executor...", end=" ")
        from task_executor import TaskExecutor
        print("✅")
        
        print("Импортируем agent...", end=" ")
        from agent import AIAgent
        print("✅")
        
        print("\n✅ Все импорты успешны!\n")
        return True
    except Exception as e:
        print(f"\n❌ Ошибка импорта: {e}\n")
        return False

def test_config():
    """Проверить конфигурацию"""
    print("=" * 60)
    print("⚙️  ПРОВЕРКА КОНФИГУРАЦИИ")
    print("=" * 60)
    
    try:
        from config import (
            OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_CONNECT_TIMEOUT,
            OLLAMA_CHAT_TIMEOUT, DEBUG, SCREENSHOT_DIR
        )
        
        print(f"Ollama Host: {OLLAMA_HOST}")
        print(f"Модель: {OLLAMA_MODEL}")
        print(f"Connect Timeout: {OLLAMA_CONNECT_TIMEOUT}s")
        print(f"Chat Timeout: {OLLAMA_CHAT_TIMEOUT}s")
        print(f"Debug: {DEBUG}")
        print(f"Screenshot Dir: {SCREENSHOT_DIR}")
        
        # Проверить директории
        from pathlib import Path
        if Path(SCREENSHOT_DIR).exists():
            print(f"✅ Директория {SCREENSHOT_DIR} существует\n")
        else:
            print(f"⚠️  Директория {SCREENSHOT_DIR} не существует (создастся автоматически)\n")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}\n")
        return False

def test_phone_connection():
    """Проверить подключение телефона"""
    print("=" * 60)
    print("📱 ПРОВЕРКА ПОДКЛЮЧЕНИЯ ТЕЛЕФОНА")
    print("=" * 60)
    
    try:
        from executor import Executor
        
        executor = Executor()
        if executor.driver.check_phone():
            print("✅ Телефон подключен!\n")
            return True
        else:
            print("❌ Телефон не подключен\n")
            print("Проверьте:")
            print("- USB кабель подключен")
            print("- Режим разработчика включен")
            print("- Отладка по USB разрешена")
            print("- Разрешение доступа к устройству было дано\n")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}\n")
        return False

def test_ollama_connection():
    """Проверить подключение к Ollama"""
    print("=" * 60)
    print("🤖 ПРОВЕРКА ПОДКЛЮЧЕНИЯ OLLAMA")
    print("=" * 60)
    
    try:
        from agent import AIAgent
        from config import OLLAMA_HOST, OLLAMA_MODEL
        
        print(f"Подключение к {OLLAMA_HOST}...")
        agent = AIAgent()
        
        if agent.is_ready():
            print("✅ Ollama доступна!\n")
            return True
        else:
            print("❌ Ollama недоступна\n")
            print("Проверьте:")
            print("- Ollama запущена? (ollama run qwen3-vl:4b)")
            print(f"- Адрес правильный? ({OLLAMA_HOST})")
            print(f"- Модель загружена? ({OLLAMA_MODEL})\n")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}\n")
        print("Убедитесь что Ollama запущена:\n  ollama run qwen3-vl:4b\n")
        return False

def test_vision_analyzer():
    """Проверить VisionAnalyzer"""
    print("=" * 60)
    print("👁️  ПРОВЕРКА VISION ANALYZER")
    print("=" * 60)
    
    try:
        from vision import VisionAnalyzer
        
        vision = VisionAnalyzer()
        print("✅ VisionAnalyzer инициализирован\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}\n")
        print("Проверьте:")
        print("- Установлена ли pytesseract? (pip install pytesseract)")
        print("- Установлен ли Tesseract OCR? (https://github.com/UB-Mannheim/tesseract)")
        print("- Установлена ли opencv-python? (pip install opencv-python)\n")
        return False

def test_task_executor():
    """Проверить TaskExecutor"""
    print("=" * 60)
    print("🎯 ПРОВЕРКА TASK EXECUTOR")
    print("=" * 60)
    
    try:
        from task_executor import TaskExecutor
        from vision import VisionAnalyzer
        from executor import Executor
        
        executor = Executor()
        vision = VisionAnalyzer()
        task_exec = TaskExecutor(executor, vision)
        
        print(f"✅ TaskExecutor инициализирован")
        print(f"   Max iterations: {task_exec.max_iterations}")
        print(f"   Iteration delay: {task_exec.iteration_delay}s\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}\n")
        return False

def main():
    """Главная функция тестирования"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "🔬 ТЕСТ PhoneDriverPP" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = []
    
    # Запустить тесты
    results.append(("Импорты", test_imports()))
    results.append(("Конфигурация", test_config()))
    results.append(("Телефон", test_phone_connection()))
    results.append(("Ollama", test_ollama_connection()))
    results.append(("Vision Analyzer", test_vision_analyzer()))
    results.append(("Task Executor", test_task_executor()))
    
    # Итоги
    print("=" * 60)
    print("📊 РЕЗУЛЬТАТЫ")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print()
    print(f"Пройдено: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!\n")
        print("Теперь вы можете запустить:")
        print("  python main.py\n")
        return 0
    else:
        print(f"\n❌ Пройдено {passed}/{total} тестов\n")
        print("Исправьте ошибки выше перед использованием проекта\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
