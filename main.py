"""
Main - точка входа приложения
"""

import time
from config import validate_config, DEBUG
from executor import Executor
from agent import AIAgent
from memory import global_memory, Action, ScreenState
from vision import VisionAnalyzer
from task_executor import TaskExecutor

def print_header():
    """Печать заголовка"""
    print("\n" + "="*60)
    print("🤖 PHONE DRIVER AI - Phase 1 Foundation")
    print("="*60)

def print_menu():
    """Печать меню команд"""
    print("\n" + "-"*60)
    print("КОМАНДЫ:")
    print("  help          - показать помощь")
    print("  status        - проверить статус")
    print("  test          - тестировать компоненты")
    print("  analyze       - анализировать экран (OCR + элементы + LLM)")
    print("  screenshot    - сделать скриншот")
    print("  tap X Y       - тап по координатам")
    print("  text 'msg'    - ввести текст")
    print("  swipe_up      - свайп вверх")
    print("  swipe_down    - свайп вниз")
    print("  back          - нажать Назад")
    print("  home          - нажать Home")
    print("  open APP      - открыть приложение (Chrome, Settings, etc)")
    print("  history       - показать историю действий")
    print("  task 'DESC'   - выполнить задачу через ИИ (напр: task 'открой Twitter')")
    print("  <текст>       - выполнить задачу через ИИ без префикса")
    print("  exit          - выход")
    print("-"*60)

def execute_command(cmd: str, executor: Executor, agent: AIAgent, vision_analyzer=None):
    """Выполнить команду"""
    raw_cmd = cmd.strip()
    cmd_lower = raw_cmd.lower()

    if not raw_cmd:
        return True

    # Системные команды
    if cmd_lower == "help":
        print_menu()
        return True

    if cmd_lower == "status":
        print("\n📊 СТАТУС:")
        print("  Телефон: ✅ Подключен")
        print(f"  AI Агент: {'✅ Готов' if agent.is_ready() else '❌ Ошибка'}")
        w, h = executor.get_screen_size()
        print(f"  Экран: {w}x{h}")
        stats = global_memory.get_stats()
        print(f"  Выполнено действий: {stats['total_actions']}")
        return True

    if cmd_lower == "test":
        print("\n🧪 ТЕСТИРОВАНИЕ КОМПОНЕНТОВ...")
        agent.test_connection()
        print("\n✅ Тест завершён")
        return True

    if cmd_lower == "analyze":
        if not vision_analyzer:
            print("❌ Vision analyzer не инициализирован")
            return True
        print("🔍 Анализ экрана...")
        try:
            desc = vision_analyzer.build_screen_description(executor)

            print("\n" + "=" * 60)
            print("📊 РЕЗУЛЬТАТЫ АНАЛИЗА")
            print("=" * 60)

            print(f"\n📝 Распознанный текст ({len(desc['ocr_text'])} символов):")
            text_preview = desc["ocr_text"][:500]
            print(text_preview + ("..." if len(desc["ocr_text"]) > 500 else ""))

            print(f"\n🔎 Найдено элементов: {len(desc['elements'])}")
            for i, elem in enumerate(desc["elements"][:10], 1):
                print(
                    f"  {i}. {elem['id']}: x={elem['x']}, y={elem['y']}, w={elem['w']}, h={elem['h']}, area={elem['area']}"
                )
            if len(desc["elements"]) > 10:
                print(f"  ... и ещё {len(desc['elements']) - 10}")

            print("\n🤖 Анализ от LLM:")
            llm_result = desc["llm"]
            if "error" in llm_result:
                print(f"  ⚠️ Ошибка: {llm_result['error']}")
            elif llm_result.get("parsed"):
                parsed = llm_result["parsed"]
                print(f"  Summary: {parsed.get('summary', 'N/A')}")
                if "named_elements" in parsed:
                    print("  Named elements:")
                    for elem in parsed["named_elements"][:5]:
                        print(f"    - {elem.get('name', 'unknown')}: {elem.get('notes', '')}")
            else:
                print(f"  Raw: {llm_result.get('raw', 'N/A')[:200]}...")

            print("=" * 60)
            action = Action("analyze", {}, success=True)
            global_memory.push_action(action)
        except Exception as e:
            import traceback

            print(f"❌ Ошибка анализа: {e}")
            if DEBUG:
                traceback.print_exc()
        return True

    if cmd_lower == "screenshot":
        print("📸 Захват скриншота...")
        executor.screenshot()
        action = Action("screenshot", {}, success=True)
        global_memory.push_action(action)
        return True

    if cmd_lower.startswith("tap"):
        try:
            parts = cmd_lower.split()
            if len(parts) == 3:
                x, y = int(parts[1]), int(parts[2])
                executor.tap(x, y)
                action = Action("tap", {"x": x, "y": y}, success=True)
                global_memory.push_action(action)
            else:
                print("❌ Формат: tap X Y")
        except ValueError:
            print("❌ X и Y должны быть числами")
        return True

    if cmd_lower == "swipe_up":
        executor.swipe_up()
        action = Action("swipe_up", {}, success=True)
        global_memory.push_action(action)
        return True

    if cmd_lower == "swipe_down":
        executor.swipe_down()
        action = Action("swipe_down", {}, success=True)
        global_memory.push_action(action)
        return True

    if cmd_lower == "back":
        executor.back()
        action = Action("back", {}, success=True)
        global_memory.push_action(action)
        return True

    if cmd_lower == "home":
        executor.home()
        action = Action("home", {}, success=True)
        global_memory.push_action(action)
        return True

    if cmd_lower.startswith("text"):
        import re

        match = re.search(r"text ['\"]?(.+?)['\"]?$", raw_cmd, flags=re.IGNORECASE)
        if match:
            msg = match.group(1)
            executor.text(msg)
            action = Action("text", {"msg": msg}, success=True)
            global_memory.push_action(action)
        else:
            print("❌ Формат: text 'сообщение'")
        return True

    if cmd_lower.startswith("open"):
        parts = raw_cmd.split()
        if len(parts) > 1:
            app = parts[1].lower()
            executor.open_app(app)
            action = Action("open", {"app": app}, success=True)
            global_memory.push_action(action)
        else:
            print("❌ Формат: open APPNAME")
        return True

    if cmd_lower == "history":
        history = global_memory.get_history()
        print(f"\n📜 История ({len(history)} действий):")
        for i, action in enumerate(history[-10:], 1):
            print(f"  {i}. {action}")
        if len(history) > 10:
            print(f"  ... и ещё {len(history) - 10}")
        return True

    if cmd_lower == "exit":
        print("\n👋 До свидания!")
        return False

    if cmd_lower.startswith("task"):
        import re

        match = re.search(r"task\s+['\"](.+?)['\"]", raw_cmd, flags=re.IGNORECASE)
        if not match:
            match = re.search(r"task\s+(.+)$", raw_cmd, flags=re.IGNORECASE)
        if not match:
            print("❌ Формат: task 'описание'")
            return True
        task_desc = match.group(1).strip()
    else:
        # Любой другой текст трактуем как задачу для ИИ
        task_desc = raw_cmd

    if not vision_analyzer:
        print("❌ Vision analyzer не инициализирован")
        return True

    print(f"🎯 Выполнение задачи: {task_desc}")
    task_exec = TaskExecutor(executor, vision_analyzer, agent)
    result = task_exec.execute_task(task_desc)
    print("\n" + "=" * 60)
    print("📋 РЕЗУЛЬТАТЫ ВЫПОЛНЕНИЯ ЗАДАЧИ")
    print("=" * 60)
    print(f"Статус: {'✅ Успешно' if result['success'] else '❌ Не выполнено'}")
    print(f"Результат: {result['result']}")
    print(f"Итерации: {result['iterations']}/{task_exec.max_iterations}")
    print(f"Действий выполнено: {len(result['actions'])}")
    if result["actions"]:
        print("\nДействия:")
        for i, act in enumerate(result["actions"], 1):
            print(f"  {i}. {act['action'].get('type')}: {act['result']}")
    print("=" * 60)
    action = Action("task", {"description": task_desc, "success": result["success"]}, success=True)
    global_memory.push_action(action)
    return True


def main():
    """Главная функция"""
    print_header()
    
    # Проверить конфигурацию
    validate_config()
    
    # Инициализировать компоненты
    print("\n🔧 Инициализация компонентов...")
    try:
        executor = Executor()
        agent = AIAgent()
        from vision import VisionAnalyzer  # Добавлено
        vision = VisionAnalyzer()           # Добавлено
        print("✅ Все компоненты готовы")
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return
    
    # Проверить подключение телефона
    if not executor.driver.check_phone():
        print("\n⚠️  Телефон не подключен. Выходим.")
        return
    
    # Меню
    print_menu()
    
    # Основной цикл
    while True:
        try:
            cmd = input("\n> ").strip()
            if not execute_command(cmd, executor, agent, vision):  # Передаём vision
                break
            time.sleep(0.3)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Прервано пользователем")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()