#!/usr/bin/env python3
"""
Friday MQTT Central Data Hub Client
Subscribes to Friday/Vanguard event topics and optionally publishes.
"""
import paho.mqtt.client as mqtt
import json, time, sys, os, argparse
from datetime import datetime

# Load .env
ENV_FILE = "/home/krsna/friday-gateway/.env"
def load_env():
    env = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env

# Defaults
env = load_env()
MQTT_HOST = env.get("MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(env.get("MQTT_PORT", "1883"))
MQTT_USER = env.get("MQTT_USERNAME", None)
MQTT_PASS = env.get("MQTT_PASSWORD", None)
CLIENT_ID = env.get("MQTT_CLIENT_ID", "friday-gateway")
RECONNECT_MS = int(env.get("MQTT_RECONNECT_INTERVAL", "5000"))

# Topics to subscribe
DEFAULT_TOPICS = [
    ("friday/#", 0),
    ("vanguard/#", 0),
    ("deck/#", 0),
]

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"[{timestamp()}] ✓ Connected to {MQTT_HOST}:{MQTT_PORT}")
        for topic, qos in DEFAULT_TOPICS:
            client.subscribe(topic, qos)
            print(f"  Subscribed: {topic}")
    else:
        print(f"[{timestamp()}] ✗ Connection failed, rc={rc}")

def on_disconnect(client, userdata, flags, rc, properties=None):
    print(f"[{timestamp()}] ✗ Disconnected, rc={rc}")
    print(f"  Reconnecting in {RECONNECT_MS}ms...")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"\n[{timestamp()}] ← {msg.topic}")
        print(f"  {json.dumps(payload, indent=2)}")
    except Exception:
        print(f"\n[{timestamp()}] ← {msg.topic} (raw): {msg.payload.decode()}")

def on_publish(client, userdata, mid, properties=None):
    print(f"[{timestamp()}] → Published mid={mid}")

def timestamp():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def publish(topic, payload_dict, qos=0, retain=False):
    msg = json.dumps(payload_dict, default=str)
    result = client.publish(topic, msg, qos, retain)
    print(f"[{timestamp()}] → Published to {topic} (mid={result.mid})")
    return result

def main():
    parser = argparse.ArgumentParser(description="Friday MQTT Client")
    parser.add_argument("--host", default=MQTT_HOST, help="MQTT broker host")
    parser.add_argument("--port", type=int, default=MQTT_PORT, help="MQTT broker port")
    parser.add_argument("--pub", nargs=3, metavar=("TOPIC", "EVENT_TYPE", "MESSAGE"),
                        help="Publish a message: TOPIC EVENT_TYPE MESSAGE")
    parser.add_argument("--subscribe", action="store_true", help="Subscribe to topics (default)")
    parser.add_argument("--keepalive", type=int, default=60, help="Keepalive interval")
    args = parser.parse_args()

    client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv5)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_publish = on_publish

    if MQTT_USER and MQTT_PASS:
        client.username_pw_set(MQTT_USER, MQTT_PASS)

    client.connect(args.host, args.port, keepalive=args.keepalive)

    if args.pub:
        topic, event_type, message = args.pub
        publish(topic, {
            "agent": "friday",
            "event_type": event_type,
            "payload": {"message": message},
            "timestamp": timestamp(),
            "version": "1.0",
            "source": CLIENT_ID
        })
    else:
        client.loop_start()
        print(f"[{timestamp()}] Friday MQTT client running. Press Ctrl+C to exit.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n[{timestamp()}] Exiting...")
        finally:
            client.loop_stop()
            client.disconnect()

if __name__ == "__main__":
    main()
