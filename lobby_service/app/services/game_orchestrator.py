import subprocess
import sys
import os
import time
from pathlib import Path
from typing import Dict, List
import json

if os.environ.get("DOCKER_ENV"):
    BASE_DIR = Path("/app")
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class GameOrchestrator:
    def __init__(self):
        # Теперь нам нужны пути к папкам сервисов, а не к файлам
        self.engine_dir = BASE_DIR / "game_engine_chess"
        self.mock_dir = BASE_DIR / "stand_mock_service"
        
        self.active_processes: Dict[str, Dict] = {}

    def start_test_game(self, game_id: str, white_id: str, black_id: str, scenario: str):
        print(f"[ORCHESTRATOR] Запуск игры {game_id}...")
        processes = []
        
        # 1. Запуск Игрового Движка как модуля
        p_engine = subprocess.Popen([
            sys.executable, "-m", "app.main", 
            "--game-id", game_id,
            "--stand-ids", white_id, black_id
        ], cwd=str(self.engine_dir)) 
        processes.append(p_engine)

        print("[ORCHESTRATOR] Ожидание инициализации движка...")
        time.sleep(2)

        # 2. Запуск моков как модулей
        for role, stand_id in [("white", white_id), ("black", black_id)]:
            p_mock = subprocess.Popen([
                sys.executable, "-m", "app.main",
                "--game-id", game_id,
                "--stand-id", stand_id,
                "--role", role,
                "--scenario", scenario
            ], cwd=str(self.mock_dir))
            processes.append(p_mock)
        
        self.active_processes[game_id] = {
            "processes": processes,
            "stands": [white_id, black_id]
        }
        print(f"[ORCHESTRATOR] Все процессы для {game_id} запущены.")

    def stop_game(self, game_id: str, reason: str = "finished"):
        if game_id not in self.active_processes: 
            return
        
        data = self.active_processes.pop(game_id)
        for p in data["processes"]:
            try:
                p.terminate()
                p.wait(timeout=1)
            except:
                try: p.kill()
                except: pass

        from app.services.mqtt_listener import lobby_mqtt
        lobby_mqtt.client.publish(f"game/{game_id}/state", b"", retain=True)
        
        print(f"[ORCHESTRATOR] Игра {game_id} завершена. Стенды свободны.")
        
    def is_stand_busy(self, stand_id: str) -> bool:
        for game_data in self.active_processes.values():
            if stand_id in game_data.get("stands", []):
                return True
        return False
    
orchestrator = GameOrchestrator()