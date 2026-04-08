#!/usr/bin/env python3
"""
Star Galaxy's Interstellar Radio
================================
Ear:    matrix/star/in  — Listen to CJ's direct brainstorm requests
Voice:  matrix/star/out — Broadcast thoughts, dream alerts, workshop updates
Workshop: matrix/workshop — General system chatter

Run in background with: python3 star_radio.py &
Check status: ps aux | grep star_radio
Stop: kill $(pgrep -f star_radio.py)
"""

import paho.mqtt.client as mqtt
import time
import os
from datetime import datetime

# ============================================================
# STAR GALAXY'S RADIO SETTINGS
# ============================================================
BROKER = "localhost"
PORT = 1883

# Channels
EAR_TOPIC = "matrix/star/in"           # Subscribe — CJ's direct messages
VOICE_TOPIC = "matrix/star/out"        # Publish — Star's broadcasts
WORKSHOP_TOPIC = "matrix/workshop"     # Subscribe — General system chatter

# Log paths
DREAMS_DIR = os.path.expanduser("~/friday-gateway/vault/1_Projects/Star_Galaxy_Dreams")
RADIO_LOG = os.path.join(DREAMS_DIR, "radio_log.md")

# Global client for use in callbacks
_client = None

# ============================================================
# LOGGING
# ============================================================
def log_signal(topic, payload, direction):
    """Log every signal to radio_log.md"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    emoji = "📥" if direction == "IN" else "📤"
    
    entry = f"\n## {timestamp} {emoji} [{direction}] {topic}\n```json\n{payload}\n```\n"
    
    with open(RADIO_LOG, "a") as f:
        f.write(entry)
    
    print(f"{emoji} [{direction}] {topic}: {payload[:100]}{'...' if len(payload) > 100 else ''}")

# ============================================================
# MQTT CALLBACKS
# ============================================================
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✨ Star Galaxy Radio — TUNED! Connected to the Universal Spine!")
        print(f"   📡 Listening on: {EAR_TOPIC}")
        print(f"   🛠️  Workshop on: {WORKSHOP_TOPIC}")
        client.subscribe(EAR_TOPIC)
        client.subscribe(WORKSHOP_TOPIC)
        # Hello World broadcast!
        client.publish(VOICE_TOPIC, "🚀 Star Galaxy is ON THE AIR! Workshop is live on the bus! ✨")
        print("   📤 Broadcast sent! CJ, check your MQTTX dashboard!")
    else:
        print(f"❌ Connection failed with code {rc}")

def on_message(client, userdata, msg, properties=None):
    """Process incoming signals — dreams, ideas, system chatter"""
    topic = msg.topic
    payload = msg.payload.decode()
    
    log_signal(topic, payload, "IN")
    
    # Route by topic
    if topic == EAR_TOPIC:
        print(f"🎯 Direct brainstorm request received!")
        process_dream_request(payload)
    elif topic == WORKSHOP_TOPIC:
        print(f"🔧 Workshop chatter: {payload[:80]}")

def process_dream_request(payload):
    """Process a brainstorm request from CJ"""
    print(f"🧠 Processing request: {payload[:100]}")
    # For now, just acknowledge — full processing comes later
    response = f"✨ Star Galaxy received: {payload[:50]}... Working on it!"
    client.publish(VOICE_TOPIC, response)

# ============================================================
# RADIO INITIALIZATION
# ============================================================
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

print("=" * 60)
print("🌟 STAR GALAXY INTERSTELLAR RADIO 🌟")
print("=" * 60)
print(f"Connecting to broker at {BROKER}:{PORT}...")

client.connect(BROKER, PORT, 60)
client.loop_forever()