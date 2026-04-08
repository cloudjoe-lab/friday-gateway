#!/usr/bin/env python3
"""Subscribe to MQTT topics and print all incoming messages."""
import paho.mqtt.client as mqtt, json, time, sys

received = []

def on_connect(c, u, f, rc, props=None):
    if rc != 0:
        print(f"Connection failed rc={rc}")
        sys.exit(1)
    # Subscribe to everything
    c.subscribe("#", qos=2)
    print("Subscribed to ALL topics (#)")

def on_message(c, u, msg):
    print(f"[{msg.timestamp}] {msg.topic}: {msg.payload[:200]}")
    received.append((msg.topic, msg.payload))

c = mqtt.Client(
    client_id="friday-mqtt-listener",
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
)
c.on_connect = on_connect
c.on_message = on_message
c.connect("127.0.0.1", 1883, keepalive=30)
c.loop_start()

print("Listening for 10 seconds...")
time.sleep(10)
c.loop_stop()
print(f"\nTotal messages received: {len(received)}")
