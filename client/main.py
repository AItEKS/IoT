# main.py
import Config as config
import requests
from Client import StandClient
from Chess import ChessRenderer

def register_stand_via_http():
    """Регистрация стенда в Lobby Service (FastAPI)"""
    print(f"Отправка PIN кода в лобби: {config.PIN_CODE}")
    url = f"{config.API_BASE_URL}/api/v1/stands/register-pin"
    payload = {"stand_id": config.STAND_ID, "pin_code": config.PIN_CODE}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Стенд успешно зарегистрирован по API!")
        else:
            print(f"Внимание при регистрации: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Бэкенд недоступен ({url}): {e}. Убедись, что docker-compose up запущен.")

def main():
    print("Инициализация AR Chess Стенда...")
    
    # 1. Стучимся в HTTP API для регистрации (согласно README)
    register_stand_via_http()
    
    # 2. Подготавливаем графику
    renderer = ChessRenderer(config)
    
    def update_board(fen, color):
        renderer.update_board_from_fen(fen, color)
        
    # 3. Стартуем MQTT клиент
    client = StandClient(config, on_board_update=update_board)
    client.connect()
    
    print("Окно графики запущено. Ожидание привязки в Dashboard...")
    
    # 4. Рендерим доску в главном потоке
    while True:
        renderer.render_loop()

if __name__ == "__main__":
    main()

# def main():
#     # калиборуемся камерой и выводим результат
#     pipeline = CalibrationPipeline()

#     cap = cv2.VideoCapture(0)
#     _, image = cap.read()
#     cv2.imwrite("calibration.jpg", image)

#     if not pipeline.process_image(image):
#         raise RuntimeError("couldn't detect calibration")

#     print(f'calibration finished {pipeline._rows}x{pipeline._cols}')

#     # создаем топик и регистрируем стенд
#     publisher = MQTTPublisher(
#         broker_host=BROCKER_HOST,
#         broker_port=BROCKER_PORT,
#         client_id=STAND_ID
#     )
#     publisher.connect()

#     publisher.client.subscribe(f'stands/{STAND_ID}/command', qos=2)
#     game_id=""

#     try:
#         while True:
#             topic = f"game/{game_id}/{STAND_ID}/markers"
#             ret, frame = cap.read()
#             data = pipeline.get_json_data(frame)
#             payload = json.loads(data)

#             publisher.publish_data(topic, payload)
#             time.sleep(DELAY)

#     except KeyboardInterrupt:
#         pass
#     finally:
#         publisher.disconnect()
#         cap.release()

# if __name__ == "__main__":
#     main()