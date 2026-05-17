import paho.mqtt.client as mqtt
import json
import time

class GameMQTTClient:
    """
    Класс для инкапсуляции всей MQTT-логики для игрового движка.
    Умеет подписываться на сообщения и публиковать состояние.
    """
    def __init__(self, broker_host: str, broker_port: int, client_id: str = ""):
        self.broker_host = broker_host
        self.broker_port = broker_port
        if not client_id:
            client_id = f"game-engine-{int(time.time())}"
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=client_id)
        self.client.on_message = self.on_message
        self.message_callback = None

    def connect(self):
        """Подключается к MQTT брокеру."""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            print(f"Game Engine: Успешное подключение к MQTT брокеру {self.broker_host}:{self.broker_port}")
        except Exception as e:
            print(f"Game Engine: Ошибка подключения к MQTT: {e}")
            exit(1)

    def on_message(self, client, userdata, msg):
        """
        Внутренний обработчик сообщений от paho-mqtt.
        Декодирует сообщение и вызывает внешний callback.
        """
        topic = msg.topic
        try:
            payload_str = msg.payload.decode('utf-8')
            payload_json = json.loads(payload_str)
            print(f"\n получено сообщение из топика: {topic}")

            if self.message_callback:
                self.message_callback(topic, payload_json)
        except json.JSONDecodeError:
            print(f"Ошибка декодирования JSON из топика {topic}: {msg.payload}")
        except Exception as e:
            print(f"Ошибка при обработке сообщения: {e}")

    def subscribe_to_stands(self, game_id: str, callback):
        """
        Подписывается на топики маркеров всех стендов в игре.
        """
        self.message_callback = callback
        topic = f"game/{game_id}/+/markers"
        self.client.subscribe(topic)
        print(f"Подписка на топик: {topic}")

    def publish_game_state(self, game_id: str, state_payload: dict):
        """
        Публикует общее состояние игры.
        """
        topic = f"game/{game_id}/state"
        json_payload = json.dumps(state_payload, indent=2)
        self.client.publish(topic, json_payload)
        print(f" -> Опубликовано общее состояние в топик '{topic}'")

    def loop_forever(self):
        """Запускает бесконечный цикл обработки сообщений."""
        print("Игровой движок запущен и ждет сообщений...")
        self.client.loop_forever()
