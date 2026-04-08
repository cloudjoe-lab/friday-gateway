#!/usr/bin/env python3
"""
Paperclip MQTT Bridge
=====================
Subscribes to MQTT topics for Vanguard commands and forwards them to Paperclip
via the HTTP adapter (webhook endpoint). Publishes Vanguard status back to MQTT.

Topics:
  friday/command/vanguard  → Paperclip HTTP adapter (POST)
  vanguard/status/#         → republished to friday/vanguard/status/#

Environment:
  MQTT_BROKER_HOST  (default: 127.0.0.1)
  MQTT_BROKER_PORT  (default: 1883)
  MQTT_KEEPALIVE    (default: 60)
  PAPERCLIP_API_URL (default: http://localhost:3100/api)
  BRIDGE_LOG_LEVEL  (default: INFO)
"""

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

import paho.mqtt.client as mqtt

# ─── Logging ────────────────────────────────────────────────────────────────

log = logging.getLogger("mqtt-bridge")
fmt = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def setup_logging():
    lvl = getattr(logging, os.getenv("BRIDGE_LOG_LEVEL", "INFO").upper())
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(fmt)
    log.addHandler(h)
    log.setLevel(lvl)


setup_logging()

# ─── Config ────────────────────────────────────────────────────────────────

MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", "60"))

PAPERCLIP_API = os.getenv("PAPERCLIP_API_URL", "http://localhost:3100/api")

BRIDGE_ID = "paperclip-mqtt-bridge"

# Topics to watch
CMD_TOPIC = "friday/command/vanguard"      # commands FROM Friday TO Vanguard
VANGUARD_STATUS_TOPIC = "vanguard/status/#" # status FROM Vanguard


# ─── MQTT Callbacks ─────────────────────────────────────────────────────────

@dataclass
class BridgeState:
    connected: bool = False
    reconnect_delay: int = 5
    max_reconnect_delay: int = 60


state = BridgeState()


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        log.info(f"Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
        state.connected = True
        state.reconnect_delay = 5
        # Subscribe to command topic
        client.subscribe(CMD_TOPIC)
        log.info(f"Subscribed: {CMD_TOPIC}")
        # Subscribe to Vanguard status
        client.subscribe(VANGUARD_STATUS_TOPIC)
        log.info(f"Subscribed: {VANGUARD_STATUS_TOPIC}")
    elif rc == 1:
        log.error("Connection refused: incorrect protocol version")
    elif rc == 2:
        log.error("Connection refused: invalid client identifier")
    elif rc == 3:
        log.error("Connection refused: server unavailable")
    elif rc == 5:
        log.warning("Connection refused: not authorised (check MQTT credentials)")
    else:
        log.error(f"Connection failed with result code {rc}")


def on_disconnect(client, userdata, rc, properties=None):
    state.connected = False
    if rc == 0:
        log.info("Disconnected gracefully")
    else:
        log.warning(f"Unexpected disconnect (rc={rc}). Reconnecting in {state.reconnect_delay}s…")
        schedule_reconnect(client)


def on_subscribe(client, userdata, mid, reasoncodes, properties=None):
    log.debug(f"Subscribed (mid={mid})")


def on_unsubscribe(client, userdata, mid, properties=None, reasoncodes=None):
    log.debug(f"Unsubscribed (mid={mid})")


def on_message(client, userdata, msg: mqtt.MQTTMessage):
    topic = msg.topic
    payload_bytes = msg.payload
    print(f"[BRIDGE DEBUG] RAW MQTT on_message: topic={topic!r} payload={payload_bytes[:80]!r}", flush=True)
    log.debug(f"MQTT ← {topic}: {payload_bytes[:200]!r}")

    # ── Command from Friday → Vanguard ──────────────────────────────────
    if topic == CMD_TOPIC:
        print(f"[BRIDGE DEBUG] Received on CMD_TOPIC: {payload_bytes[:100]}", flush=True)
        handle_vanguard_command(topic, payload_bytes)

    # ── Status from Vanguard → forward to friday namespace ─────────────
    elif topic.startswith("vanguard/status"):
        forward_to_friday(topic, payload_bytes)

    else:
        log.debug(f"Topic not handled: {topic}")


def handle_vanguard_command(topic: str, payload_bytes: bytes):
    """Forward a Vanguard command to the Paperclip HTTP adapter → triggers Vanguard heartbeat."""
    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        log.warning(f"Invalid JSON on {topic}: {e}")
        return

    log.info(f"Vanguard command received: {payload.get('action', 'unknown')}")
    log.debug(f"  payload: {payload}")

    # ── POST to Paperclip heartbeat/invoke to wake Vanguard ──────────────────
    import urllib.request
    import urllib.error

    VANGUARD_AGENT_ID = os.getenv("PAPERCLIP_VANGUARD_AGENT_ID", "e01f2661-a18b-4052-8a00-e7ffa3d2a764")
    COMPANY_ID       = os.getenv("PAPERCLIP_COMPANY_ID", "ac4b993d-2d80-4d2b-8527-6bb0e1d5d25e")

    invoke_url = f"{PAPERCLIP_API}/agents/{VANGUARD_AGENT_ID}/heartbeat/invoke"

    invoke_payload = {
        "source": "mqtt_bridge",
        "triggerDetail": "friday_command",
        "payload": payload,
    }

    try:
        req = urllib.request.Request(
            invoke_url,
            data=json.dumps(invoke_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            log.info(f"Vanguard heartbeat/invoke → status {resp.status}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        log.warning(f"heartbeat/invoke HTTP {e.code}: {body[:200]}")
    except Exception as ex:
        log.error(f"Failed to invoke Vanguard: {ex}")


def forward_to_friday(topic: str, payload_bytes: bytes):
    """Republish Vanguard status under the Friday namespace."""
    # Map vanguard/status → friday/vanguard/status
    new_topic = topic.replace("vanguard/status", "friday/vanguard/status", 1)
    result = client.publish(new_topic, payload_bytes, qos=1)
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        log.debug(f"Republished to {new_topic}")
    else:
        log.warning(f"Failed to republish to {new_topic}: {result.rc}")


# ─── Reconnection ───────────────────────────────────────────────────────────

_reconnect_task: Optional[asyncio.Task] = None


def schedule_reconnect(client):
    global _reconnect_task
    if _reconnect_task and not _reconnect_task.done():
        return

    def _reconnect():
        log.info(f"Attempting reconnect in {state.reconnect_delay}s…")
        time.sleep(state.reconnect_delay)
        try:
            client.reconnect()
        except Exception as e:
            log.error(f"Reconnect error: {e}")
            state.reconnect_delay = min(
                state.reconnect_delay * 2, state.max_reconnect_delay
            )
            schedule_reconnect(client)

    import threading
    t = threading.Thread(target=_reconnect, daemon=True)
    t.start()


# ─── Publish convenience ────────────────────────────────────────────────────

def mqtt_publish(topic: str, payload: dict, qos: int = 1, retain: bool = False):
    """Publish a dict payload to an MQTT topic."""
    if not state.connected:
        log.warning(f"Cannot publish to {topic}: not connected")
        return
    data = json.dumps(payload, ensure_ascii=False)
    result = client.publish(topic, data, qos=qos, retain=retain)
    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        log.warning(f"Publish to {topic} failed: {result.rc}")


# ─── Main ──────────────────────────────────────────────────────────────────

client = mqtt.Client(
    client_id=BRIDGE_ID,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_subscribe = on_subscribe
client.on_unsubscribe = on_unsubscribe
client.on_message = on_message

# Optional: MQTT username/password from env
if os.getenv("MQTT_USERNAME"):
    client.username_pw_set(
        os.getenv("MQTT_USERNAME"),
        os.getenv("MQTT_PASSWORD", ""),
    )

# Optional: TLS
if os.getenv("MQTT_TLS", "0") == "1":
    client.tls_set()


def run():
    log.info(f"Starting Paperclip MQTT Bridge (broker={MQTT_HOST}:{MQTT_PORT})")
    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=MQTT_KEEPALIVE)
    except Exception as e:
        log.error(f"Cannot connect to MQTT broker: {e}")
        sys.exit(1)

    client.loop_forever()


if __name__ == "__main__":
    run()
