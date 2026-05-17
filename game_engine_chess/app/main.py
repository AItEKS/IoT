import argparse
import json
import os
import time
import threading
from app.services.mqtt_client import GameMQTTClient
from app.core.logic import ChessGame

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-id", required=True)
    parser.add_argument("--stand-ids", nargs='+', required=True)
    parser.add_argument("--broker", default=os.environ.get("MQTT_BROKER_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("MQTT_BROKER_PORT", 1883)))
    args = parser.parse_args()

    game = ChessGame(args.stand_ids[0], args.stand_ids[1])
    mqtt = GameMQTTClient(args.broker, args.port)
    mqtt.connect()

    # Фоновая задача для мягкого завершения игры
    def finalize_game(game_id, reason):
        print(f"[ENGINE] МАТ! Ждем 1.5 секунды перед закрытием...")
        # 1. Даем фронтенду 1.5 секунды, чтобы отрисовать победу
        time.sleep(1.5)
        
        # 2. Публикуем приказ Лобби на закрытие игры
        mqtt.client.publish(
            "lobby/game_over", 
            json.dumps({"game_id": game_id, "reason": reason})
        )
        
        # 3. Даем пакету полсекунды физически уйти в сеть
        time.sleep(0.5)
        
        # 4. Жестко убиваем процесс движка
        os._exit(0)

    def on_msg(topic, payload):
        sid = topic.split('/')[2]
        
        # Обновляем логику
        if game.update_stand_state(sid, payload.get("matrix", [])):
            state = game.get_visual_state()
            
            # Публикуем состояние доски (НИКАКИХ БЛОКИРОВОК!)
            mqtt.client.publish(f"game/{args.game_id}/state", json.dumps(state))
            
            if game.state == "GAME_OVER":
                # Запускаем финал в отдельном потоке, чтобы MQTT продолжил работать
                threading.Thread(
                    target=finalize_game, 
                    args=(args.game_id, state["game_status"])
                ).start()

    mqtt.subscribe_to_stands(args.game_id, on_msg)
    mqtt.loop_forever()

if __name__ == "__main__":
    main()