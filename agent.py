"""
Agent - ядро AI агента, интеграция с Ollama
"""

import json

import requests

try:
    from ollama import Ollama
except Exception:
    Ollama = None

from config import (
    DEBUG,
    OLLAMA_CHAT_TIMEOUT,
    OLLAMA_CONNECT_TIMEOUT,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OLLAMA_API_KEY,
)

class OllamaClient:
    """Клиент для взаимодействия с локальной Ollama"""
    
    def __init__(self, host: str = OLLAMA_HOST, model: str = OLLAMA_MODEL):
        self.host = host
        self.model = model
        self.client = None
        # If official ollama client is available, instantiate it for cleaner calls
        if Ollama is not None:
            try:
                self.client = Ollama(host=self.host, api_key=OLLAMA_API_KEY or None)
                if DEBUG:
                    print("🔌 Используется ollama Python client")
            except Exception:
                self.client = None
        self.api_url = f"{host}/api/chat"
        self.connected = False
        self._check_connection()
    
    def _check_connection(self):
        """Проверить подключение к Ollama"""
        try:
            headers = {}
            if OLLAMA_API_KEY:
                headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
            response = requests.get(f"{self.host}/api/tags", timeout=OLLAMA_CONNECT_TIMEOUT, headers=headers)
            if response.status_code == 200:
                self.connected = True
                if DEBUG:
                    print(f"✅ Ollama подключена: {self.host}")
                return True
        except requests.exceptions.ConnectionError:
            print(f"❌ Ошибка: Ollama не найдена на {self.host}")
            print("   Запустите: ollama serve")
            self.connected = False
            return False
    
    def send_message(self, prompt: str, system_prompt: str = None) -> str:
        """
        Отправить сообщение в LLM
        
        Args:
            prompt: Основной запрос
            system_prompt: Системный промпт (инструкции агенту)
        
        Returns:
            str: Ответ от LLM
        """
        if not self.connected:
            return "❌ Ollama не подключена"
        
        try:
            headers = {"Content-Type": "application/json"}
            if OLLAMA_API_KEY:
                headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "messages": [
                        *([
                            {"role": "system", "content": system_prompt}
                        ] if system_prompt else []),
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False
                },
                headers=headers,
                timeout=OLLAMA_CHAT_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result.get("message", {})
                return message.get("content", result.get("response", ""))
            else:
                return f"❌ Ошибка {response.status_code}: {response.text}"
        
        except requests.exceptions.Timeout:
            return "❌ Timeout: LLM слишком долго отвечает"
        except Exception as e:
            return f"❌ Ошибка: {str(e)}"

class AIAgent:
    """AI Агент для автоматизации"""
    
    SYSTEM_PROMPT = """Ты - автоматизационный агент для управления Android телефоном.
Твоя задача - понять пожелание пользователя и разбить его на простые действия.

Доступные действия:
- tap X Y - нажать по координатам (X, Y)
- swipe_up - свайп вверх
- swipe_down - свайп вниз
- text "..." - ввести текст
- back - нажать кнопку Назад
- home - нажать кнопку Home
- screenshot - сделать скриншот
- open APP - открыть приложение (Chrome, Settings, etc)

Всегда отвечай в формате:
ACTION: [действие]
PARAMS: [параметры если нужны]

Будь кратким и точным."""
    
    def __init__(self):
        self.ollama = OllamaClient()
        if DEBUG:
            print("✅ AI Agent инициализирован")
    
    def is_ready(self) -> bool:
        """Проверить, готов ли агент"""
        return self.ollama.connected
    
    def process_command(self, user_command: str) -> str:
        """
        Обработать команду пользователя
        
        Args:
            user_command: Текст команды пользователя
        
        Returns:
            str: Действие для выполнения
        """
        response = self.ollama.send_message(
            prompt=f"Команда пользователя: {user_command}",
            system_prompt=self.SYSTEM_PROMPT
        )
        return response
    
    def test_connection(self):
        """Протестировать подключение"""
        print("\n" + "="*50)
        print("ТЕСТ AI АГЕНТА")
        print("="*50)
        if self.is_ready():
            print("✅ Ollama подключена")
            print(f"🤖 Модель: {self.ollama.model}")
            
            # Простой тест
            test_response = self.ollama.send_message("Привет! Кто ты?")
            print(f"\n📝 Тестовый ответ:\n{test_response[:200]}...")
        else:
            print("❌ Ollama не подключена!")
        print("="*50)

if __name__ == "__main__":
    agent = AIAgent()
    agent.test_connection()
