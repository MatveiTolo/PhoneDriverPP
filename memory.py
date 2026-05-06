"""
Memory - управление состоянием и историей действий
"""

from typing import List, Dict
from datetime import datetime
from config import DEBUG

class ScreenState:
    """Состояние экрана"""
    
    def __init__(self):
        self.screenshot_path = None
        self.ocr_text = ""  # Будет заполнено на Фазе 2
        self.detected_elements = []  # Будет заполнено на Фазе 2
        self.timestamp = datetime.now()
    
    def __repr__(self):
        return f"ScreenState(screenshot={self.screenshot_path}, timestamp={self.timestamp})"

class Action:
    """Запись о выполненном действии"""
    
    def __init__(self, action_type: str, params: Dict = None, success: bool = True):
        self.type = action_type  # 'tap', 'text', 'swipe_up', etc.
        self.params = params or {}
        self.success = success
        self.timestamp = datetime.now()
    
    def __repr__(self):
        return f"Action({self.type}, params={self.params}, success={self.success})"

class TaskMemory:
    """Память о текущей задаче"""
    
    def __init__(self):
        self.actions: List[Action] = []
        self.screen_history: List[ScreenState] = []
        self.task_description = ""
        self.start_time = datetime.now()
    
    def push_action(self, action: Action):
        """Добавить действие в историю"""
        self.actions.append(action)
        if DEBUG:
            print(f"📝 {action}")
    
    def push_screen_state(self, state: ScreenState):
        """Добавить состояние экрана"""
        self.screen_history.append(state)
    
    def get_history(self) -> List[Action]:
        """Получить историю действий"""
        return self.actions.copy()
    
    def get_screen_history(self) -> List[ScreenState]:
        """Получить историю скриншотов"""
        return self.screen_history.copy()
    
    def clear(self):
        """Очистить память (новая задача)"""
        self.actions.clear()
        self.screen_history.clear()
        self.task_description = ""
        self.start_time = datetime.now()
    
    def set_task(self, description: str):
        """Установить описание задачи"""
        self.task_description = description
    
    def get_stats(self) -> Dict:
        """Получить статистику"""
        return {
            "total_actions": len(self.actions),
            "successful_actions": sum(1 for a in self.actions if a.success),
            "screen_captures": len(self.screen_history),
            "duration": (datetime.now() - self.start_time).total_seconds()
        }

# Глобальная память
global_memory = TaskMemory()

if __name__ == "__main__":
    mem = TaskMemory()
    mem.set_task("Test task")
    mem.push_action(Action("tap", {"x": 100, "y": 200}))
    mem.push_action(Action("text", {"msg": "Hello"}))
    print(mem.get_stats())
