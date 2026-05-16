"""
Vision Pipeline - OCR + OpenCV + LLM анализ экрана
"""

import base64
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import pytesseract
import requests

try:
    from ollama import Ollama
except Exception:
    Ollama = None

from config import (
    DEBUG,
    OLLAMA_CHAT_TIMEOUT,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OLLAMA_API_KEY,
    SCREENSHOT_DIR,
)

# Ensure directories
THUMBS_DIR = Path(SCREENSHOT_DIR) / "thumbs"
THUMBS_DIR.mkdir(parents=True, exist_ok=True)


class VisionAnalyzer:
    """Анализатор визуального содержимого экрана"""

    def __init__(self, tesseract_lang: str = None):
        self.tesseract_lang = tesseract_lang or "rus+eng"
        if DEBUG:
            print(f"✅ VisionAnalyzer инициализирован (Tesseract: {self.tesseract_lang})")

    def _timestamp_name(self) -> str:
        return f"shot_{int(time.time())}.png"

    def capture_screenshot(self, executor) -> str:
        """
        Захватить скриншот через ADB и вернуть локальный путь.
        Использует ADB команды напрямую через executor.send_command().
        """
        screenshot_dir = Path(SCREENSHOT_DIR)
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        name = self._timestamp_name()
        local_path = screenshot_dir / name

        executor.send_command("adb shell screencap -p /sdcard/s.png")
        executor.send_command(f'adb pull /sdcard/s.png "{local_path}"')
        executor.send_command("adb shell rm /sdcard/s.png")

        if not local_path.exists():
            raise FileNotFoundError(f"Скриншот не найден: {local_path}")

        if DEBUG:
            print(f"📸 Скриншот сохранён: {local_path}")
        return str(local_path)

    def extract_text_ocr(self, image_path: str) -> Tuple[str, List[Dict]]:
        """
        Извлечь текст и bbox'ы с помощью pytesseract.
        Возвращает (full_text, words_list) где words_list: [{text, x, y, w, h, conf}, ...]
        """
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Изображение не загружено: {image_path}")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=1.0, fy=1.0, interpolation=cv2.INTER_LINEAR)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        custom_oem_psm_config = f"-l {self.tesseract_lang} --psm 3"
        data = pytesseract.image_to_data(thresh, config=custom_oem_psm_config, output_type=pytesseract.Output.DICT)

        words = []
        full_text_lines = []
        n_boxes = len(data.get("text", []))
        for i in range(n_boxes):
            txt = str(data["text"][i]).strip()
            conf_val = data.get("conf", [None] * n_boxes)[i]
            try:
                conf = int(conf_val)
            except Exception:
                try:
                    conf = int(float(conf_val))
                except Exception:
                    conf = -1

            if txt:
                x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                words.append({"text": txt, "x": int(x), "y": int(y), "w": int(w), "h": int(h), "conf": conf})
                full_text_lines.append(txt)

        full_text = "\n".join(full_text_lines)
        if DEBUG:
            print(f"🔤 OCR: {len(words)} слов, текст длиной {len(full_text)}")
        return full_text, words

    def analyze_ui_elements(self, image_path: str, min_area: int = 1000) -> List[Dict]:
        """
        Обнаружить потенциальные UI-элементы (кнопки, панели) через OpenCV.
        Возвращает список элементов: {id, x, y, w, h, area, aspect, thumb}
        """
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Изображение не загружено: {image_path}")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.bilateralFilter(gray, 9, 75, 75)
        edges = cv2.Canny(blur, 50, 150)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        edges = cv2.dilate(edges, kernel, iterations=1)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        elements = []
        idx = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            aspect = w / (h + 1e-6)
            if w < 30 or h < 20:
                continue
            idx += 1

            thumb = img[y : y + h, x : x + w]
            thumb_name = THUMBS_DIR / f"thumb_{int(time.time())}_{idx}.png"
            cv2.imwrite(str(thumb_name), thumb)

            elements.append({
                "id": f"el_{idx}",
                "x": int(x),
                "y": int(y),
                "w": int(w),
                "h": int(h),
                "area": int(area),
                "aspect": float(aspect),
                "thumb": str(thumb_name),
            })

        elements = sorted(elements, key=lambda e: e["area"], reverse=True)
        if DEBUG:
            print(f"🔎 Найдено элементов: {len(elements)}")
        return elements

    def _thumbnail_b64(self, image_path: str, max_size: Tuple[int, int] = (300, 300)) -> str:
        img = cv2.imread(image_path)
        if img is None:
            return ""
        h, w = img.shape[:2]
        scale = min(max_size[0] / (w or 1), max_size[1] / (h or 1), 1.0)
        if scale < 1.0:
            img = cv2.resize(img, (int(w * scale), int(h * scale)))
        _, buf = cv2.imencode(".png", img)
        b64 = base64.b64encode(buf.tobytes()).decode("utf-8")
        return b64

    def _image_b64(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def _extract_json_from_text(self, text: str):
        if not text or not isinstance(text, str):
            return None
        text = text.strip()
        try:
            return json.loads(text)
        except Exception:
            pass
        import re

        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        return None

    def send_to_llm_for_analysis(self, image_path: str, ocr_text: str, elements: List[Dict]) -> Dict:
        """
        Отправить данные в Ollama и получить структурированный анализ.
        Возвращает dict с ключами summary, named_elements.
        """
        prompt = {
            "title": "Screen analysis request",
            "ocr_preview": ("\n".join(ocr_text.splitlines()[:20]) or "<no_text>"),
            "elements": [
                {"id": e["id"], "x": e["x"], "y": e["y"], "w": e["w"], "h": e["h"]}
                for e in elements[:20]
            ],
            "instruction": (
                "Опиши кратко, что видно на экране, и предложи имена для основных элементов "
                "(например: search_box, profile_button, tweet_item). Верни ответ в JSON формате: "
                '{"summary": "...", "named_elements":[{"name":"search_box","id":"el_1","notes":"..."}]}'
            ),
        }

        user_prompt = (
            "Проанализируй этот экран мобильного устройства.\n"
            "Используй изображение, OCR и найденные элементы.\n"
            "Верни только JSON без пояснений в формате: "
            '{"summary":"...","named_elements":[{"name":"...","id":"el_1","notes":"..."}]}\n\n'
            f"CONTEXT:\n{json.dumps(prompt, ensure_ascii=False, indent=2)}"
        )

        api_url = f"{OLLAMA_HOST}/api/chat"
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Ты — анализатор экрана мобильного приложения. "
                        "Отвечай ТОЛЬКО одним JSON-объектом на русском языке, без пояснений, без markdown. "
                        "Формат: {\"summary\":\"...\", \"named_elements\": [{\"name\":\"...\", \"id\":\"el_1\", \"notes\":\"...\"}]}"
                    ),
                },
                {
                    "role": "user",
                    "content": user_prompt,
                    "images": [
                        self._image_b64(image_path)
                        if ("localhost" in OLLAMA_HOST or "127.0.0.1" in OLLAMA_HOST)
                        else self._thumbnail_b64(image_path)
                    ],
                },
            ],
            "stream": False,
            "temperature": 0,
        }

        headers = {"Content-Type": "application/json"}
        if OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

        try:
            if Ollama is not None:
                try:
                    client = Ollama(host=OLLAMA_HOST, api_key=OLLAMA_API_KEY or None)
                    res = client.chat(model=OLLAMA_MODEL, messages=payload.get("messages"), timeout=OLLAMA_CHAT_TIMEOUT)
                    if isinstance(res, dict):
                        res_json = res
                    else:
                        try:
                            res_json = res.__dict__
                        except Exception:
                            res_json = {"message": {"content": str(res)}}
                except Exception:
                    resp = requests.post(api_url, json=payload, headers=headers, timeout=OLLAMA_CHAT_TIMEOUT)
                    if resp.status_code != 200:
                        return {"error": f"LLM returned {resp.status_code}: {resp.text}"}
                    res_json = resp.json()
            else:
                resp = requests.post(api_url, json=payload, headers=headers, timeout=OLLAMA_CHAT_TIMEOUT)
                if resp.status_code != 200:
                    return {"error": f"LLM returned {resp.status_code}: {resp.text}"}
                res_json = resp.json()

            text = res_json.get("message", {}).get("content") or ""
            parsed = self._extract_json_from_text(text)
            if parsed is not None:
                return {"raw": text, "parsed": parsed}

            return {"raw": text, "parsed": None}

        except requests.exceptions.Timeout:
            return {
                "error": (
                    f"Timeout waiting for Ollama after {OLLAMA_CHAT_TIMEOUT}s. "
                    "Модель, вероятно, ещё загружается или работает слишком медленно."
                )
            }
        except Exception as e:
            return {"error": str(e)}

    def build_screen_description(self, executor, include_llm: bool = True, include_ocr_elements: bool = True) -> Dict:
        """
        Полный пайплайн:
        1) Захват скриншота
        2) OCR (опционально)
        3) Детекция элементов (опционально)
        4) Опциональная отправка в LLM для семантического анализа
        5) Сбор и возврат структуры
        """
        path = self.capture_screenshot(executor)
        ocr_text = ""
        words = []
        elements = []

        if include_ocr_elements:
            ocr_text, words = self.extract_text_ocr(path)
            elements = self.analyze_ui_elements(path)

        llm_result = self.send_to_llm_for_analysis(path, ocr_text, elements) if include_llm else {}

        screen_desc = {
            "screenshot": path,
            "ocr_text": ocr_text,
            "words": words,
            "elements": elements,
            "llm": llm_result,
            "timestamp": int(time.time()),
        }

        try:
            from memory import global_memory, ScreenState

            state = ScreenState()
            state.screenshot_path = path
            state.ocr_text = ocr_text
            state.detected_elements = elements
            global_memory.push_screen_state(state)
            if DEBUG:
                print("🧠 ScreenState сохранён в память")
        except Exception:
            if DEBUG:
                print("⚠️ Не удалось сохранить ScreenState (memory модуль недоступен)")

        return screen_desc


if __name__ == "__main__":
    print("Пример использования VisionAnalyzer (нужен запущенный executor и подключённый телефон)")
