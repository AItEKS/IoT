# iot_client.py
import paho.mqtt.client as mqtt
import json
import time
import threading
import cv2

from Detection import CalibrationPipeline

class StandClient:
    def __init__(self, config, on_board_update):
        self.config = config
        self.client = mqtt.Client(client_id=self.config.STAND_ID)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        self.on_board_update = on_board_update
        self.active_game_id = None
        self.is_playing = False
        self.last_sent_state = None
        
        # Подключаем камеру
        self.cap = cv2.VideoCapture(0)
        self.pipeline = CalibrationPipeline()
        
        calib_file = "calibration_data.json"
        
        # Пытаемся загрузить старую калибровку
        if self.pipeline.load_calibration(calib_file):
            print(f"Загружена сохраненная калибровка {self.pipeline._rows}x{self.pipeline._cols}")
        else:
            print("Файл калибровки не найден. Запуск алгоритма калибровки...")
            # Читаем кадр с камеры для калибровки
            # Сбрасываем первые пару кадров, пока камера "просыпается" и настраивает фокус/свет
            for _ in range(5):
                self.cap.read()
                time.sleep(0.1)
                
            ret, image = self.cap.read()
            if not ret or not self.pipeline.process_image(image):
                raise RuntimeError("Не удалось обнаружить маркеры калибровки! Проверьте освещение и пустую доску.")
                
            cv2.imwrite("calibration.jpg", image)
            print(f"Калибровка успешно завершена {self.pipeline._rows}x{self.pipeline._cols}")
            
            # Сохраняем результат
            self.pipeline.save_calibration(calib_file)
        ret, frame = self.cap.read()
        self.pipeline.get_json_data(frame)


    def connect(self):
        self.client.connect(self.config.BROKER_ADDRESS, self.config.BROKER_PORT, 60)
        self.client.loop_start()
        
    def on_connect(self, client, userdata, flags, rc):
        print(f"MQTT Подключен! Слушаем команды для стенда {self.config.STAND_ID}...")
        # 1. Подписка на команды от Lobby Orchestrator
        self.client.subscribe(f"stands/{self.config.STAND_ID}/commands")
        
    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        # Слушаем команды управления стендом
        if topic == f"stands/{self.config.STAND_ID}/commands":
            data = json.loads(payload)
            
            if data.get("action") == "start_game":
                self.active_game_id = data.get("game_id")
                role = data.get("role")
                print(f"Получена команда start_game! Game ID: {self.active_game_id}, Роль: {role}")
                
                # 2. Подписываемся на состояние конкретной игры
                self.client.subscribe(f"game/{self.active_game_id}/state")
                
                # Запускаем отправку данных от камеры в отдельном потоке
                self.is_playing = True
                threading.Thread(target=self.send_markers_loop, daemon=True).start()
                
        # Слушаем состояние игры (от Game Engine)
        elif self.active_game_id and topic == f"game/{self.active_game_id}/state":
            try:
                data = json.loads(payload)
                if "fen" in data:
                    # Парсим FEN: вторая часть строки FEN (например, "w" или "b") — это активный цвет
                    fen_parts = data["fen"].split(' ')
                    active_color = fen_parts[1] if len(fen_parts) > 1 else 'w'
                    
                    # Передаем и доску, и цвет в рендерер
                    self.on_board_update(data["fen"], active_color)
            except Exception as e:
                print(f"Ошибка парсинга: {e}")
        

    def send_markers_loop(self):
        """Симулирует отправку данных с камеры / Aruco маркеров"""
        topic = f"game/{self.active_game_id}/{self.config.STAND_ID}/markers"
        
        # Словарь для хранения "счетчика стабильности" каждого маркера
        # Формат: { marker_id: count_of_frames_seen }
        self.marker_stability = {}
        # Порог стабильности (сколько кадров подряд маркер должен быть виден)
        STABILITY_THRESHOLD = 5 
        
        self.last_sent_state = None
        
        while self.is_playing:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue
                
            # Получаем все детекции из текущего кадра
            current_data = self.pipeline.get_board_data(frame)
            
            # Находим, какие маркеры видны на ЭТОМ кадре
            visible_ids = {m.id for m in current_data}
            
            # Обновляем счетчики:
            # 1. Для видимых увеличиваем счетчик
            for m in current_data:
                self.marker_stability[m.id] = self.marker_stability.get(m.id, 0) + 1
            
            # 2. Для исчезнувших сбрасываем счетчик (или уменьшаем)
            # Если маркер пропал, мы "не верим" в его исчезновение сразу
            # и ждем пару кадров, либо сбрасываем сразу
            for m_id in list(self.marker_stability.keys()):
                if m_id not in visible_ids:
                    self.marker_stability[m_id] = 0 # Сбрасываем доверие, если пропал
            
            # Формируем список "стабильных" маркеров
            stable_markers =[
                m for m in current_data 
                if self.marker_stability.get(m.id, 0) >= STABILITY_THRESHOLD
            ]
            
            # Сортируем для сравнения
            stable_markers_sorted = sorted(stable_markers, key=lambda x: x.id)
            
            # Преобразуем в список словарей для сравнения с кэшем
            current_payload_matrix = [m.dict() for m in stable_markers_sorted]
            
            # Отправляем, только если состояние стабильно и оно отличается от прошлого
            if current_payload_matrix != self.last_sent_state:
                # Дополнительная проверка: если мы только что "стабилизировали" маркер,
                # отправляем данные.
                payload = {"matrix": current_payload_matrix}
                self.client.publish(topic, json.dumps(payload))
                self.last_sent_state = current_payload_matrix
                print("Стабильное состояние отправлено.")
            
            time.sleep(0.2) # Уменьшили задержку, так как фильтрация теперь внутри