"""
Task Executor - выполнение пользовательских задач через ИИ
"""

import json
import time
from typing import Dict, List, Optional

import requests

try:
    from ollama import Ollama
except Exception:
    Ollama = None

from config import DEBUG, OLLAMA_CHAT_TIMEOUT, OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_API_KEY


class TaskExecutor:
    """Выполняет пользовательские задачи через анализ экрана и ИИ"""

    def __init__(self, executor, vision_analyzer, agent=None):
        """
        :param executor: Executor - управление ADB командами
        :param vision_analyzer: VisionAnalyzer - анализ экрана
        :param agent: AIAgent - опционально для логирования
        """
        self.executor = executor
        self.vision_analyzer = vision_analyzer
        self.agent = agent
        self.max_iterations = 15
        self.iteration_delay = 1.0  # секунды между итерациями
        self.action_history: List[Dict] = []

    def execute_task(self, task_description: str) -> Dict:
        """
        Выполнить задачу на основе текстового описания.

        :param task_description: Описание задачи (например: "открой Twitter и найди пользователя @user")
        :return: {"success": bool, "result": str, "iterations": int, "actions": [...]}
        """
        if DEBUG:
            print(f"\n🎯 НАЧАЛО ВЫПОЛНЕНИЯ ЗАДАЧИ: {task_description}")

        self.action_history = []
        iteration = 0
        task_completed = False
        result_message = "Выполнено"

        while iteration < self.max_iterations and not task_completed:
            iteration += 1
            if DEBUG:
                print(f"\n--- Итерация {iteration}/{self.max_iterations} ---")

            try:
                # 1. Захватить скриншот
                desc = self.vision_analyzer.build_screen_description(
                    self.executor,
                    include_llm=False,
                    include_ocr_elements=False,
                )

                # 2. Получить следующее действие от LLM
                action_result = self._get_next_action(
                    task_description=task_description,
                    screen_description=desc,
                    iteration=iteration,
                    previous_actions=self.action_history,
                )

                if "error" in action_result:
                    if DEBUG:
                        print(f"❌ Ошибка получения действия: {action_result['error']}")
                    result_message = f"Ошибка: {action_result['error']}"
                    break

                # 3. Извлечь действие из ответа
                action = action_result.get("action")
                reasoning = action_result.get("reasoning", "")
                task_completed = bool(action_result.get("task_completed", False))
                status = action_result.get("status", "выполняется")

                if DEBUG:
                    print(f"💭 Рассуждение: {reasoning}")
                    print(f"📋 Статус: {status}")

                # 4. Выполнить действие (если есть)
                if action and not task_completed:
                    exec_result = self._execute_action(action, desc)
                    if DEBUG:
                        print(f"✅ Действие: {action.get('type')} → {exec_result}")

                    self.action_history.append({
                        "iteration": iteration,
                        "action": action,
                        "result": exec_result,
                    })

                    # Небольшая задержка перед следующей итерацией
                    time.sleep(self.iteration_delay)

                elif task_completed:
                    if DEBUG:
                        print(f"✅ ЗАДАЧА ВЫПОЛНЕНА на итерации {iteration}")
                    result_message = status or "Задача успешно выполнена"

            except Exception as e:
                result_message = f"Ошибка выполнения: {e}"
                if DEBUG:
                    print(f"❌ {result_message}")
                break

        return {
            "success": task_completed,
            "result": result_message,
            "iterations": iteration,
            "actions": self.action_history,
        }

    def _get_next_action(
        self,
        task_description: str,
        screen_description: Dict,
        iteration: int,
        previous_actions: List[Dict],
    ) -> Dict:
        """Запросить следующее действие у модели"""
        actions_history_str = "\n".join(
            [
                f"  [{a['iteration']}] {a['action'].get('type', '?')}: {a['result']}"
                for a in previous_actions[-5:]
            ]
        )

        user_prompt = (
            f"ЗАДАЧА: {task_description}\n"
            f"Итерация: {iteration}\n\n"
            "ТЕКУЩЕЕ СОСТОЯНИЕ ЭКРАНА: смотри изображение ниже.\n\n"
        )

        if actions_history_str:
            user_prompt += f"ИСТОРИЯ ДЕЙСТВИЙ:\n{actions_history_str}\n\n"

        screen_w, screen_h = self.executor.get_screen_size()
        user_prompt += (
            "ИНСТРУКЦИЯ: Проанализируй экран и верни JSON с ключами:\n"
            "- reasoning: краткое объяснение анализа (на русском)\n"
            "- action: объект действия (type: 'tap'|'text'|'swipe'|'back'|'home'|'open'|'wait'|null, "
            "x_norm/y_norm/text/direction/app/seconds по необходимости)\n"
            "- task_completed: true если задача выполнена\n"
            "- status: статус выполнения задачи\n"
            f"Размер экрана: {screen_w}x{screen_h}. "
            "Для tap используй НОРМАЛИЗОВАННЫЕ координаты: x_norm и y_norm (0..1).\n"
            "Правила точности: выбирай центр целевого элемента (кнопки/иконки/поля), "
            "избегай границ и соседних элементов.\n"
            "Для swipe можешь указать start_x_norm/start_y_norm/end_x_norm/end_y_norm (0..1) "
            "или использовать direction: up/down — тогда свайп пройдет через центр экрана.\n"
            "Если сомневаешься, сначала сделай короткий безопасный свайп или тап по крупной кнопке.\n"
            "После каждого действия ориентируйся только на новый скриншот, "
            "чтобы понять завершена задача или нужен ещё шаг.\n"
            "Верни ТОЛЬКО корректный JSON без пояснений.\n"
            "Пример: {"  # noqa: ISC003 - part of literal
            "\"reasoning\":\"...\",\"action\":{\"type\":\"tap\",\"x_norm\":0.5,\"y_norm\":0.9},"
            "\"task_completed\":false,\"status\":\"выполняется\"}"
        )

        api_url = f"{OLLAMA_HOST}/api/chat"
        image_path = screen_description.get("screenshot")
        images = []
        if image_path:
            if ("localhost" in OLLAMA_HOST or "127.0.0.1" in OLLAMA_HOST):
                images = [self.vision_analyzer._image_b64(image_path)]
            else:
                images = [self.vision_analyzer._thumbnail_b64(image_path)]

        messages = [
            {
                "role": "system",
                "content": (
                    "Ты — помощник для автоматизации действий на экране мобильного устройства. "
                    "Отвечай ТОЛЬКО корректным JSON на русском языке, без пояснений, без markdown."
                ),
            },
            {"role": "user", "content": user_prompt, "images": images},
        ]

        res_json = self._call_ollama(api_url, messages)
        if "error" in res_json:
            return {"error": res_json["error"]}

        text = (
            res_json.get("message", {}).get("content")
            or res_json.get("response")
            or res_json.get("output")
            or res_json.get("result")
            or ""
        )

        parsed = self._extract_json_from_text(text)
        if parsed:
            return parsed

        # Если не распарсили — follow-up с просьбой вернуть JSON
        follow_payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": "Преобразуй в корректный JSON объект."},
                {
                    "role": "user",
                    "content": (
                        "Верни только JSON объект с ключами: reasoning, action, task_completed, status. "
                        f"Предыдущий ответ:\n{text}"
                    ),
                },
            ],
            "stream": False,
            "temperature": 0,
        }

        headers = {"Content-Type": "application/json"}
        if OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

        try:
            resp2 = requests.post(api_url, json=follow_payload, headers=headers, timeout=OLLAMA_CHAT_TIMEOUT)
            if resp2.status_code == 200:
                text2 = resp2.json().get("message", {}).get("content", "")
                parsed2 = self._extract_json_from_text(text2)
                if parsed2:
                    return parsed2
        except Exception:
            pass

        return {
            "reasoning": "Не смог распарсить ответ модели, ожидание...",
            "action": {"type": "wait"},
            "task_completed": False,
            "status": "ошибка парсинга",
        }

    def _call_ollama(self, api_url: str, messages: List[Dict]) -> Dict:
        headers = {"Content-Type": "application/json"}
        if OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

        if Ollama is not None:
            try:
                client = Ollama(host=OLLAMA_HOST, api_key=OLLAMA_API_KEY or None)
                res = client.chat(model=OLLAMA_MODEL, messages=messages, timeout=OLLAMA_CHAT_TIMEOUT)
                if isinstance(res, dict):
                    return res
                try:
                    return res.__dict__
                except Exception:
                    return {"message": {"content": str(res)}}
            except Exception:
                pass

        try:
            resp = requests.post(
                api_url,
                json={"model": OLLAMA_MODEL, "messages": messages, "stream": False, "temperature": 0},
                headers=headers,
                timeout=OLLAMA_CHAT_TIMEOUT,
            )
            if resp.status_code != 200:
                return {"error": f"LLM returned {resp.status_code}: {resp.text}"}
            return resp.json()
        except requests.exceptions.Timeout:
            return {"error": f"Timeout waiting for LLM ({OLLAMA_CHAT_TIMEOUT}s)"}
        except Exception as e:
            return {"error": str(e)}

    def _extract_json_from_text(self, text: str) -> Optional[Dict]:
        """Извлечь JSON из текста модели"""
        if not text:
            return None

        text = text.strip()
        try:
            return json.loads(text)
        except Exception:
            pass

        # Попытка найти {...}
        import re

        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass

        return None

    def _execute_action(self, action: Dict, screen_description: Dict) -> str:
        """
        Выполнить действие на телефоне.

        :param action: {"type": "tap"/"text"/"swipe"/"back"/"home"/"open"/"wait", ...}
        :return: Описание результата действия
        """
        action_type = action.get("type", "wait")

        try:
            if action_type == "tap":
                if "x_norm" in action and "y_norm" in action:
                    w, h = self.executor.get_screen_size()
                    x = int(float(action.get("x_norm", 0)) * w)
                    y = int(float(action.get("y_norm", 0)) * h)
                elif "x" in action and "y" in action:
                    x = int(action.get("x", 0))
                    y = int(action.get("y", 0))
                else:
                    return "❌ Для tap нужны координаты x_norm/y_norm"

                self.executor.tap(x, y)
                return f"tap({x}, {y})"

            if action_type == "text":
                text = action.get("text", "")
                self.executor.text(text)
                return f"text('{text}')"

            if action_type == "swipe":
                if {
                    "start_x_norm",
                    "start_y_norm",
                    "end_x_norm",
                    "end_y_norm",
                }.issubset(action.keys()):
                    w, h = self.executor.get_screen_size()
                    x1 = int(float(action.get("start_x_norm", 0)) * w)
                    y1 = int(float(action.get("start_y_norm", 0)) * h)
                    x2 = int(float(action.get("end_x_norm", 0)) * w)
                    y2 = int(float(action.get("end_y_norm", 0)) * h)
                    self.executor.swipe(x1, y1, x2, y2)
                    return f"swipe({x1}, {y1}) -> ({x2}, {y2})"

                direction = action.get("direction", "up").lower()
                w, h = self.executor.get_screen_size()
                center_x = w // 2
                start_y = int(h * 0.7)
                end_y = int(h * 0.35)
                if direction == "up":
                    self.executor.swipe(center_x, start_y, center_x, end_y)
                    return "swipe_up"
                if direction == "down":
                    self.executor.swipe(center_x, end_y, center_x, start_y)
                    return "swipe_down"
                return f"❌ Неизвестное направление swipe: {direction}"

            if action_type == "back":
                self.executor.back()
                return "back"

            if action_type == "home":
                self.executor.home()
                return "home"

            if action_type == "open":
                app = action.get("app", "")
                if not app:
                    return "❌ Не указан app для открытия"
                self.executor.open_app(app)
                return f"open('{app}')"

            if action_type == "wait":
                seconds = float(action.get("seconds", 1))
                time.sleep(max(seconds, 0))
                return f"wait({seconds}s)"

            return f"❌ Неизвестный тип действия: {action_type}"

        except Exception as e:
            return f"❌ Ошибка выполнения: {str(e)}"
