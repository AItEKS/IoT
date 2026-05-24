import argparse
import json
import os
import time
import threading
import sys
from app.services.mqtt_client import GameMQTTClient
from app.core.logic import ChessGame

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-id", required=True)
    parser.add_argument("--stand-ids", nargs='+', required=True)
    parser.add_argument("--broker", default="mqtt")
    args = parser.parse_args()

    game = ChessGame(args.stand_ids[0], args.stand_ids[1])
    mqtt = GameMQTTClient(args.broker, 1883)
    mqtt.connect()

    def finalize_game(game_id, reason):
        print(f"[ENGINE] Finalizing game {game_id} (Reason: {reason})")
        time.sleep(1.5)
        mqtt.client.publish("lobby/game_over", json.dumps({"game_id": game_id, "reason": reason}))
        time.sleep(0.5)
        os._exit(0)

    def on_msg(topic, payload):
        sid = topic.split('/')[2]
        if game.update_stand_state(sid, payload.get("matrix", [])):
            state = game.get_visual_state()
            mqtt.client.publish(f"game/{args.game_id}/state", json.dumps(state))
            if game.state == "GAME_OVER":
                threading.Thread(target=finalize_game, args=(args.game_id, state["game_status"])).start()

    mqtt.subscribe_to_stands(args.game_id, on_msg)
    
    print(f"[ENGINE] Engine online for {args.game_id}")
    mqtt.client.publish(f"game/{args.game_id}/state", json.dumps(game.get_visual_state()))
    
    mqtt.loop_forever()

if __name__ == "__main__":
    main()