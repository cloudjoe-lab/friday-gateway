#!/usr/bin/env python3
"""Quick MQTT pub/sub test — verifies the bridge relay works."""
import paho.mqtt.client as mqtt, time, json, sys

TEST_TOPIC = "friday/command/vanguard"
RESPONSE_TOPIC = "friday/test/response"

results = []

def on_connect(c, u, f, rc, properties=None):
    if rc != 0:
        print(f"Connection failed rc={rc}")
        sys.exit(1)
    c.subscribe(RESPONSE_TOPIC)
    time.sleep(0.3)
    c.publish(TEST_TOPIC, json.dumps({"action":"ping","test":True,"ts":time.time()}), qos=1)
    print(f"Published ping to {TEST_TOPIC}")

def on_message(c, u, msg):
    print(f"Received on {msg.topic}: {msg.payload[:200]}")
    results.append(msg.payload)
    c.disconnect()
    c.loop_stop()

c = mqtt.Client(
    client_id="friday-test-client",
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
)
c.on_connect = on_connect
c.on_message = on_message

c.connect("127.0.0.1", 1883, keepalive=15)
c.loop_forever()
print("Done — results:", len(results))
