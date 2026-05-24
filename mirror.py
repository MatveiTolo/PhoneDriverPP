#!/usr/bin/env python3
"""
Скрипт для запуска трансляции экрана телефона на ПК.
Запускает scrcpy из папки scrcpy/, которая лежит рядом со скриптом.
"""

import subprocess
import sys
import os

def find_and_run_scrcpy():
    # Получаем путь к папке, где находится этот скрипт (корень PhoneDriverPP)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Путь к scrcpy.exe внутри папки scrcpy/
    scrcpy_path = os.path.join(script_dir, "scrcpy", "scrcpy.exe")
    
    # Проверяем, существует ли файл
    if not os.path.exists(scrcpy_path):
        print(f"❌ Ошибка: Не найден {scrcpy_path}")
        print("Убедитесь, что:")
        print("  1. Папка 'scrcpy' существует в корне репозитория")
        print("  2. Внутри папки 'scrcpy' есть файл scrcpy.exe")
        print("  3. Файл называется именно scrcpy.exe (не scrpy.exe)")
        sys.exit(1)
    
    print(f"✅ Найден scrcpy по пути: {scrcpy_path}")
    print("📱 Запускаем трансляцию экрана...")
    print("Совет: закройте окно scrcpy, чтобы остановить трансляцию.\n")
    
    try:
        # Запускаем scrcpy. --no-audio отключает звук для стабильности.
        process = subprocess.Popen(
            [scrcpy_path, "--no-audio"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        print("Трансляция запущена!")
        print("Нажмите Ctrl+C в этой консоли, чтобы остановить трансляцию.\n")
        
        # Ожидаем завершения процесса scrcpy (пока пользователь не закроет окно)
        process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Получен сигнал остановки. Завершаем трансляцию...")
        process.terminate()
        process.wait()
    except Exception as e:
        print(f"❌ Произошла ошибка при запуске: {e}")
        sys.exit(1)
    
    print("Трансляция остановлена.")

if __name__ == "__main__":
    find_and_run_scrcpy()