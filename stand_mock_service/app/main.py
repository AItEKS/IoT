import os
import time
import argparse
import json
from app.core.publisher import MQTTPublisher
from app.scenarios.loader import load_steps_for_role

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-id", type=str, required=True)
    parser.add_argument("--stand-id", type=str, required=True)
    parser.add_argument("--role", type=str, required=True)
    parser.add_argument("--scenario", type=str, default="realistic_mate")
    args = parser.parse_args()

    broker_host = os.environ.get("MQTT_BROKER_HOST", "mqtt")
    steps = load_steps_for_role(args.scenario, args.role)
    
    # Client ID теперь совпадает с Stand ID
    publisher = MQTTPublisher(broker_host, 1883, client_id=args.stand_id)
    publisher.connect()

    for i, step in enumerate(steps):
        topic = f"game/{args.game_id}/{args.stand_id}/markers"
        publisher.publish_data(topic, step.get("payload"))
        print(f"[{args.stand_id}] Sent step {i+1}")
        time.sleep(step.get("delay_after", 5))

    publisher.disconnect()

if __name__ == "__main__":
    main()