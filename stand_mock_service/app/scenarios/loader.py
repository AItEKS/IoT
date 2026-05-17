import json
from pathlib import Path
from typing import List, Dict, Any

def load_steps_for_role(scenario_name: str, role: str) -> List[Dict[str, Any]]:
    """
    Загружает сценарий из JSON-файла и возвращает список шагов,
    предназначенных для указанной роли ('white' или 'black').
    """
    scenario_path = Path(__file__).parent / "data" / f"{scenario_name}.json"
    
    if not scenario_path.exists():
        print(f"Ошибка: Файл сценария не найден по пути {scenario_path}")
        return []

    print(f"Загрузка сценария '{scenario_name}' для роли '{role}'...")
    
    try:
        with open(scenario_path, 'r', encoding='utf-8') as f:
            scenario_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Ошибка декодирования JSON в файле {scenario_path}: {e}")
        return []
        
    all_steps = scenario_data.get("steps", [])
    role_steps = [step for step in all_steps if step.get("role") == role]
    
    print(f"Найдено {len(role_steps)} шагов для роли '{role}'.")
    return role_steps