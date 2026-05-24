import subprocess
import sys
import os
import time
from pathlib import Path
from typing import Dict
import json

if os.environ.get("DOCKER_ENV"):
    BASE_DIR = Path("/app")
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class GameOrchestrator:
    def __init__(self):
        self.engine_dir = BASE_DIR / "game_engine_chess"
        self.mock_dir = BASE_DIR / "stand_mock_service"
        self.active_processes: Dict[str, Dict] = {}

    def start_game(self, game_id: str, white_id: str, black_id: str, scenario: str = "realistic_mate", use_mocks: bool = False):
        mqtt_host = os.getenv("MQTT_BROKER_HOST", "mqtt" if os.environ.get("DOCKER_ENV") else "localhost")
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1" 

        processes = []
        print(f"[ORCHESTRATOR] START: {game_id} | W: {white_id} | B: {black_id}")
        
        # 1. Запуск Движка
        p_engine = subprocess.Popen([
            sys.executable, "-m", "app.main", 
            "--game-id", game_id,
            "--stand-ids", white_id, black_id,
            "--broker", mqtt_host
        ], cwd=str(self.engine_dir), env=env) 
        processes.append(p_engine)

        time.sleep(2)

        # 2. Запуск моков или команд
        if use_mocks:
            for role, s_id in [("white", white_id), ("black", black_id)]:
                print(f"[ORCHESTRATOR] MOCK: {s_id}")
                p_mock = subprocess.Popen([
                    sys.executable, "-m", "app.main",
                    "--game-id", game_id,
                    "--stand-id", s_id,
                    "--role", role,
                    "--scenario", scenario
                ], cwd=str(self.mock_dir), env=env)
                processes.append(p_mock)
                time.sleep(0.5)
        else:
            from app.services.mqtt_listener import lobby_mqtt
            for role, s_id in [("white", white_id), ("black", black_id)]:
                command = {"action": "start_game", "game_id": game_id, "role": role}
                lobby_mqtt.client.publish(f"stands/{s_id}/commands", json.dumps(command))

        self.active_processes[game_id] = {
            "processes": processes,
            "stands": [white_id, black_id]
        }

    def stop_game(self, game_id: str, reason: str = "finished"):
        if game_id not in self.active_processes: return
        data = self.active_processes.pop(game_id)
        for p in data["processes"]:
            try: p.terminate()
            except: pass
        from app.services.mqtt_listener import lobby_mqtt
        try:
            lobby_mqtt.client.publish(f"game/{game_id}/state", b"", retain=True)
            for s_id in data["stands"]:
                lobby_mqtt.client.publish(f"stands/{s_id}/commands", json.dumps({"action": "stop_game"}))
        except: pass

    def is_stand_busy(self, stand_id: str) -> bool:
        for game_data in self.active_processes.values():
            if stand_id in game_data.get("stands", []): return True
        return False
    
    def stop_all_games(self):
        for g_id in list(self.active_processes.keys()): self.stop_game(g_id)

orchestrator = GameOrchestrator()