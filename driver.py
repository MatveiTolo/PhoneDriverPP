"""
Phone Driver - управление телефоном через ADB
"""

import subprocess
import re
import time
import os

# ПУТЬ К ВАШЕМУ ADB
ADB_PATH = r"adb"

class PhoneDriver:
    def __init__(self):
        self.check_phone()
    
    def cmd(self, command):
        """Выполняет ADB команду"""
        full_cmd = command.replace("adb", ADB_PATH, 1)
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    
    def check_phone(self):
        """Проверяет подключение телефона"""
        print("\n" + "="*40)
        print("ПРОВЕРКА ПОДКЛЮЧЕНИЯ")
        print("="*40)
        
        output = self.cmd("adb devices")
        print(output)
        
        if "device" in output and "unauthorized" not in output:
            print("\n✅ ТЕЛЕФОН ПОДКЛЮЧЕН!")
            return True
        elif "unauthorized" in output:
            print("\n❌ НАЖМИТЕ 'РАЗРЕШИТЬ' НА ТЕЛЕФОНЕ!")
            return False
        else:
            print("\n❌ ТЕЛЕФОН НЕ НАЙДЕН!")
            print("1. Включите отладку по USB")
            print("2. Подключите кабель")
            return False
    
    def tap(self, x, y):
        """Тап"""
        self.cmd(f"adb shell input tap {x} {y}")
        print(f"✅ Тап ({x}, {y})")
    
    def swipe_up(self):
        """Свайп вверх"""
        w, h = self.get_size()
        start_x = w // 2
        start_y = int(h * 0.8)
        end_y = int(h * 0.3)
        self.cmd(f"adb shell input swipe {start_x} {start_y} {start_x} {end_y}")
        print("✅ Свайп вверх")
    
    def swipe_down(self):
        """Свайп вниз"""
        w, h = self.get_size()
        start_x = w // 2
        start_y = int(h * 0.3)
        end_y = int(h * 0.8)
        self.cmd(f"adb shell input swipe {start_x} {start_y} {start_x} {end_y}")
        print("✅ Свайп вниз")

    def swipe(self, x1, y1, x2, y2):
        """Произвольный свайп"""
        self.cmd(f"adb shell input swipe {x1} {y1} {x2} {y2}")
        print(f"✅ Свайп ({x1}, {y1}) -> ({x2}, {y2})")
    
    def text(self, msg):
        """Ввод текста"""
        msg = msg.replace(" ", "%s")
        self.cmd(f'adb shell input text "{msg}"')
        print(f"✅ Текст: {msg.replace('%s', ' ')}")
    
    def back(self):
        """Назад"""
        self.cmd("adb shell input keyevent KEYCODE_BACK")
        print("✅ Назад")
    
    def home(self):
        """Домой"""
        self.cmd("adb shell input keyevent KEYCODE_HOME")
        print("✅ Домой")
    
    def get_size(self):
        """Размер экрана"""
        out = self.cmd("adb shell wm size")
        nums = re.findall(r"(\d+)", out)
        if len(nums) >= 2:
            return int(nums[0]), int(nums[1])
        return 1080, 1920
    
    def screenshot(self):
        """Скриншот"""
        if not os.path.exists("screenshots"):
            os.makedirs("screenshots")
        name = f"screenshots/shot_{int(time.time())}.png"
        self.cmd("adb shell screencap -p /sdcard/s.png")
        self.cmd(f'adb pull /sdcard/s.png "{name}"')
        self.cmd("adb shell rm /sdcard/s.png")
        print(f"✅ Скриншот: {name}")
    
    def open(self, app):
        """Открыть приложение"""
        apps = {
            "chrome": "com.android.chrome",
            "settings": "com.android.settings",
            "camera": "com.android.camera",
            "youtube": "com.google.android.youtube"
        }
        pkg = apps.get(app.lower())
        if pkg:
            self.cmd(f"adb shell monkey -p {pkg} 1")
            print(f"✅ Открыт: {app}")
        else:
            print(f"❌ Приложение '{app}' не найдено")


def main():
    driver = PhoneDriver()
    
    if not driver.check_phone():
        input("\nНажмите Enter для выхода...")
        return
    
    # Показываем меню
    while True:
        print("\n" + "-"*40)
        print("КОМАНДЫ:")
        print("  tap X Y        - тап")
        print("  up             - свайп вверх")
        print("  down           - свайп вниз")
        print("  text '...'     - ввод текста")
        print("  back           - назад")
        print("  home           - домой")
        print("  screen         - скриншот")
        print("  open chrome    - открыть Chrome")
        print("  exit           - выход")
        print("-"*40)
        
        cmd = input("\n> ").strip().lower()
        
        if cmd == "exit":
            break
        
        elif cmd.startswith("tap"):
            parts = cmd.split()
            if len(parts) == 3:
                driver.tap(int(parts[1]), int(parts[2]))
            else:
                print("❌ Формат: tap X Y")
        
        elif cmd == "up":
            driver.swipe_up()
        
        elif cmd == "down":
            driver.swipe_down()
        
        elif cmd.startswith("text"):
            match = re.search(r"text ['\"]?(.+?)['\"]?$", cmd)
            if match:
                driver.text(match.group(1))
            else:
                print("❌ Формат: text 'текст'")
        
        elif cmd == "back":
            driver.back()
        
        elif cmd == "home":
            driver.home()
        
        elif cmd == "screen":
            driver.screenshot()
        
        elif cmd.startswith("open"):
            parts = cmd.split()
            if len(parts) > 1:
                driver.open(parts[1])
            else:
                print("❌ Формат: open chrome")
        
        else:
            print("❌ Неизвестная команда")
        
        time.sleep(0.5)

if __name__ == "__main__":
    main()