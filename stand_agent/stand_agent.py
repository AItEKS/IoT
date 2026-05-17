import time
import json
import argparse
import requests
import paho.mqtt.client as mqtt

CV_API_URL = "http://127.0.0.1:8080/data"
POLL_INTERVAL = 0.1

class StandAgent:
    def __init__(self, broker_host, broker_port, game_id, stand_id):
        self.game_id = game_id
        self.stand_id = stand_id
        self.publish_topic = f"game/{game_id}/{stand_id}/markers"
        self.subscribe_topic = f"game/{game_id}/state"
        
        self.previous_state_hash = None

        self.client = mqtt.Client(f"agent-{stand_id}")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        print(f"[AGENT] Подключение к MQTT {broker_host}:{broker_port}...")
        self.client.connect(broker_host, broker_port, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print(f"[AGENT] Успешно подключен к брокеру. Подписка на: {self.subscribe_topic}")
        self.client.subscribe(self.subscribe_topic)

    def on_message(self, client, userdata, msg):
        """
        Здесь мы получаем команды на отрисовку от Игрового Движка (из облака).
        """
        try:
            visual_data = json.loads(msg.payload.decode('utf-8'))
            print(f"\n[AGENT] Получены данные для проектора! Статус игры: {visual_data.get('game_status')}")
            
            # ==========================================
            # TODO: ИНТЕГРАЦИЯ С ПРОЕКТОРОМ
            # Здесь нужно передать `visual_data` скрипту renderer.py вашего партнера.
            # Например, если у рендерера есть локальный API:
            # requests.post("http://127.0.0.1:8081/render", json=visual_data)
            # ==========================================
            
        except Exception as e:
            print(f"[AGENT] Ошибка обработки входящего сообщения: {e}")

    def run(self):
        """Основной цикл: опрос камеры и отправка в облако."""
        print("[AGENT] Агент запущен. Начинаю опрос камеры...")
        
        while True:
            try:
                response = requests.get(CV_API_URL, timeout=1)
                
                if response.status_code == 200:
                    data = response.json()
                    matrix = data.get("matrix", [])
                    
                    sorted_matrix = sorted(matrix, key=lambda x: x.get('id', 0))
                    current_state_hash = hash(json.dumps(sorted_matrix))

                    if current_state_hash != self.previous_state_hash:
                        print(f"[AGENT] Замечено движение! Отправка в облако ({len(matrix)} маркеров)")
                        self.client.publish(self.publish_topic, json.dumps(data))
                        self.previous_state_hash = current_state_hash
                        
            except requests.exceptions.RequestException:
                pass
            except Exception as e:
                print(f"[AGENT] Ошибка в главном цикле: {e}")
                
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--broker", default="127.0.0.1", help="IP адрес MQTT брокера (облака)")
    parser.add_argument("--game-id", required=True, help="ID текущей игры")
    parser.add_argument("--stand-id", required=True, help="Мой ID стенда (напр. stand-user-egor)")
    args = parser.parse_args()

    agent = StandAgent(
        broker_host=args.broker,
        broker_port=1883,
        game_id=args.game_id,
        stand_id=args.stand_id
    )
    
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n[AGENT] Остановка работы...")
        agent.client.loop_stop()
        agent.client.disconnect()