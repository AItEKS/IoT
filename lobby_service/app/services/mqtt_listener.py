import paho.mqtt.client as mqtt
import json
import logging
from app.core.config import settings

# Настроим логгер, чтобы видеть события в консоли uvicorn
logger = logging.getLogger(__name__)

class LobbyMQTTListener:
    def __init__(self):
        # Используем современный API paho-mqtt
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION1, 
            "lobby-service-main"
        )
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def connect_and_start(self):
        try:
            self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)
            self.client.loop_start()
            logger.info(f"[LOBBY MQTT] Подключение к брокеру {settings.MQTT_BROKER_HOST}...")
        except Exception as e:
            logger.error(f"[LOBBY MQTT] Ошибка подключения: {e}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("[LOBBY MQTT] Отключен.")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("[LOBBY MQTT] Успешно подключен к брокеру.")
            # Подписываемся на топик завершения игры
            self.client.subscribe("lobby/game_over")
            logger.info("[LOBBY MQTT] Подписан на топик: lobby/game_over")
        else:
            logger.error(f"[LOBBY MQTT] Ошибка подключения, код: {rc}")

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning("[LOBBY MQTT] Неожиданное отключение. Ожидание авто-реконнекта...")

    def on_message(self, client, userdata, msg):
        # Важный момент: импортируем внутри метода, чтобы избежать циклического импорта
        from app.services.game_orchestrator import orchestrator
        
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            game_id = payload.get("game_id")
            reason = payload.get("reason", "finished") # finished, mate, aborted
            
            if game_id:
                logger.info(f"[LOBBY MQTT] Сигнал завершения: {game_id} (причина: {reason})")
                orchestrator.stop_game(game_id)
            else:
                logger.warning("[LOBBY MQTT] Получено пустое сообщение game_id")
                
        except json.JSONDecodeError:
            logger.error(f"[LOBBY MQTT] Ошибка декодирования JSON: {msg.payload}")
        except Exception as e:
            logger.error(f"[LOBBY MQTT] Ошибка обработки сообщения: {e}")

lobby_mqtt = LobbyMQTTListener()