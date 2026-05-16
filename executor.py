"""
Executor - обёртка над PhoneDriver для выполнения действий
"""

from driver import PhoneDriver
from config import DEBUG

class Executor:
    """Выполнитель действий на телефоне"""
    
    def __init__(self):
        self.driver = PhoneDriver()
        self.last_screenshot = None
        if DEBUG:
            print("✅ Executor инициализирован")
    
    def tap(self, x, y):
        """Тап по координатам"""
        self.driver.tap(x, y)
        return True
    
    def swipe_up(self):
        """Свайп вверх"""
        self.driver.swipe_up()
        return True
    
    def swipe_down(self):
        """Свайп вниз"""
        self.driver.swipe_down()
        return True

    def swipe(self, x1, y1, x2, y2):
        """Произвольный свайп"""
        self.driver.swipe(x1, y1, x2, y2)
        return True
    
    def text(self, msg):
        """Ввод текста"""
        self.driver.text(msg)
        return True
    
    def back(self):
        """Нажать 'Назад'"""
        self.driver.back()
        return True
    
    def home(self):
        """Нажать 'Home'"""
        self.driver.home()
        return True
    
    def screenshot(self):
        """Сделать скриншот"""
        self.driver.screenshot()
        return True
    
    def open_app(self, app_name):
        """Открыть приложение"""
        self.driver.open(app_name)
        return True
    
    def get_screen_size(self):
        """Получить размер экрана"""
        return self.driver.get_size()
    
    def send_command(self, cmd):
        """Отправить ADB команду"""
        return self.driver.cmd(cmd)

if __name__ == "__main__":
    executor = Executor()
    print("✅ Executor готов к работе")