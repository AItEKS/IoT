import paho.mqtt.client as mqtt
import json
import time

class MQTTPublisher:
    """
    Класс для инкапсуляции логики публикации сообщений в MQTT
    """
    def __init__(self, broker_host: str, broker_port: int, client_id: str = ""):
        self.broker_host = broker_host
        self.broker_port = broker_port

        if not client_id:
            client_id = f"stand-mock-{int(time.time())}"
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=client_id)
        print(f"Инициализирован MQTT клиент с ID: {client_id}")

    def connect(self):
        """Подключается к MQTT брокеру."""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            print(f"Успешное подключение к MQTT брокеру по адресу {self.broker_host}:{self.broker_port}")
        except ConnectionRefusedError:
            print(f"Ошибка: Не удалось подключиться к MQTT брокеру по адресу {self.broker_host}:{self.broker_port}. Проверьте, запущен ли брокер.")
            exit(1)
        except Exception as e:
            print(f"Произошла непредвиденная ошибка при подключении: {e}")
            exit(1)


    def publish_data(self, topic: str, payload: dict):
        """
        Публикует Python-словарь в указанный топик, предварительно
        конвертировав его в JSON-строку.
        """
        try:
            json_payload = json.dumps(payload, indent=2)
            result = self.client.publish(topic, json_payload)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f" -> Опубликовано в топик '{topic}'")
            else:
                print(f"Ошибка публикации в топик '{topic}', код ошибки: {result.rc}")
        except Exception as e:
            print(f"Ошибка при формировании или публикации JSON: {e}")

    def disconnect(self):
        """Корректно отключается от брокера."""
        print("Отключение от MQTT брокера...")
        self.client.loop_stop()
        self.client.disconnect()