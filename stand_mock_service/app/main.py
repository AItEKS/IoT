import os
import time
import argparse

from app.core.publisher import MQTTPublisher
from app.scenarios.loader import load_steps_for_role

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-id", type=str, required=True)
    parser.add_argument("--stand-id", type=str, required=True)
    parser.add_argument("--role", type=str, choices=['white', 'black'], required=True)
    parser.add_argument("--scenario", type=str, default="normal_game")
    
    args = parser.parse_args()

    broker_host = os.environ.get("MQTT_BROKER_HOST", "localhost")
    broker_port = int(os.environ.get("MQTT_BROKER_PORT", 1883))

    steps = load_steps_for_role(args.scenario, args.role)
    
    if not steps:
        print(f"[{args.stand_id}] Шаги для роли {args.role} не найдены.")
        return

    publisher = MQTTPublisher(
        broker_host=broker_host,
        broker_port=broker_port,
        client_id=f"mock-{args.stand_id}"
    )
    publisher.connect()

    try:
        for i, step in enumerate(steps):
            comment = step.get('comment', '...')
            payload = step.get("payload")
            delay = step.get("delay_after", 5)

            topic = f"game/{args.game_id}/{args.stand_id}/markers"
            
            print(f"[{args.stand_id}] Шаг {i+1}/{len(steps)}: {comment}")
            publisher.publish_data(topic, payload)
            
            print(f"[{args.stand_id}] Ожидание {delay}с...")
            time.sleep(delay)

        print(f"[{args.stand_id}] Сценарий завершен.")
    except KeyboardInterrupt:
        pass
    finally:
        publisher.disconnect()

if __name__ == "__main__":
    main()