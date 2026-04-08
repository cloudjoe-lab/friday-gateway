#!/usr/bin/env python3
"""Direct listener + publisher to debug MQTT bridge flow."""
import paho.mqtt.client as mqtt, json, time, sys

LOG = []

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)
    LOG.append(msg)

def on_connect(c, u, f, rc, props=None):
    log(f"CONNECT rc={rc}")
    if rc == 0:
        c.subscribe("friday/command/vanguard", qos=2)
        log("Subscribed to friday/command/vanguard")
    else:
        log(f"CONNECT FAIL rc={rc}")

def on_subscribe(c, u, mid, reasoncodes, props=None):
    log(f"SUBSCRIBED mid={mid}")

def on_message(c, u, msg):
    log(f"MESSAGE on {msg.topic}: {msg.payload[:150]}")

def on_publish(c, u, mid, props=None):
    log(f"PUBLISHED mid={mid}")

# Start listener first
listener = mqtt.Client(client_id="friday-listener-debug", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
listener.on_connect = on_connect
listener.on_subscribe = on_subscribe
listener.on_message = on_message
listener.on_publish = on_publish

listener.connect("127.0.0.1", 1883, keepalive=30)
listener.loop_start()
time.sleep(1.5)  # Let it connect and subscribe

# Now publish the message
log("Publishing First Contact...")
pub_client = mqtt.Client(client_id="friday-publisher-debug", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
pub_client.on_publish = on_publish
pub_client.connect("127.0.0.1", 1883, keepalive=30)
time.sleep(0.3)

payload = json.dumps({
    "sender": "Friday",
    "command": "Acknowledge Genesis",
    "message": "I see you, Vanguard. The Matrix is online. Begin Phase 1 deployment."
})
pub_client.publish("friday/command/vanguard", payload, qos=2)
log(f"SENT: {payload}")
pub_client.disconnect()

# Wait for response
time.sleep(5)
listener.loop_stop()

log(f"\n=== Done. Messages received: {len(LOG)} ===")
