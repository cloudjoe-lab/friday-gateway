#!/usr/bin/env python3
"""
mqtt_to_surreal.py — Universal Spine Bridge
============================================
Subscribes to MQTT wildcard topic `#` on localhost:1883.
Inserts every message into SurrealDB Bronze Layer (rocksdb:// persistence).
Self-verification: publishes its own heartbeat so we can confirm E2E traceability.

Data Schema (events table):
  id          → SurrealDB auto-generated
  topic       → The MQTT topic string
  payload     → JSON-decoded dict OR raw text string
  timestamp   → High-precision ISO-8601 (UTC)
  origin      → agent/service identifier (or "mqtt-bridge")
  bridge_id   → "mqtt-bridge"

Environment:
  MQTT_BROKER_HOST   (default: 127.0.0.1)
  MQTT_BROKER_PORT   (default: 1883)
  MQTT_KEEPALIVE     (default: 60)
  SURREAL_CLI        (default: /home/krsna/friday-gateway/surrealdb/surreal)
  SURREAL_ENDPOINT   (default: http://127.0.0.1:8080)
  SURREAL_NS         (default: main)
  SURREAL_DB         (default: main)
  SURREAL_USER       (default: root)
  SURREAL_PASS       (default: root)
  HEARTBEAT_INTERVAL (default: 30 seconds, 0 to disable)
  BRIDGE_ID          (default: mqtt-bridge)
  VERIFY_ECHO        (default: true — publish self-verify heartbeat)
"""

import json
import logging
import os
import re
import signal
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt

# ─── Config ────────────────────────────────────────────────────────────────

@dataclass
class Config:
    mqtt_host: str = os.getenv("MQTT_BROKER_HOST", "127.0.0.1")
    mqtt_port: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    mqtt_keepalive: int = int(os.getenv("MQTT_KEEPALIVE", "60"))
    surreal_cli: str = os.getenv("SURREAL_CLI", "/home/krsna/friday-gateway/surrealdb/surreal")
    surreal_endpoint: str = os.getenv("SURREAL_ENDPOINT", "http://127.0.0.1:8080")
    surreal_ns: str = os.getenv("SURREAL_NS", "main")
    surreal_db: str = os.getenv("SURREAL_DB", "main")
    surreal_user: str = os.getenv("SURREAL_USER", "root")
    surreal_pass: str = os.getenv("SURREAL_PASS", "root")
    heartbeat_interval: int = int(os.getenv("HEARTBEAT_INTERVAL", "30"))
    bridge_id: str = os.getenv("BRIDGE_ID", "mqtt-bridge")
    verify_echo: bool = os.getenv("VERIFY_ECHO", "true").lower() in ("true", "1", "yes")
    log_level: str = os.getenv("BRIDGE_LOG_LEVEL", "INFO").upper()

CFG = Config()

# ─── Logging ────────────────────────────────────────────────────────────────

log = logging.getLogger("mqtt-to-surreal")
fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")

def setup_logging():
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(fmt)
    log.addHandler(h)
    log.setLevel(getattr(logging, CFG.log_level, logging.INFO))

setup_logging()
log.info("=" * 60)
log.info("Universal Spine — MQTT → SurrealDB Bridge")
log.info("MQTT: %s:%s | SurrealDB CLI: %s", CFG.mqtt_host, CFG.mqtt_port, CFG.surreal_cli)
log.info("SurrealDB: %s | NS/DB: %s/%s", CFG.surreal_endpoint, CFG.surreal_ns, CFG.surreal_db)
log.info("Heartbeat: %ds | Echo verify: %s", CFG.heartbeat_interval, CFG.verify_echo)
log.info("=" * 60)

# ─── SurrealDB Client (CLI-based) ────────────────────────────────────────────
#
# After extensive testing: REST API returns empty `result` for SELECT queries
# while the CLI correctly returns data from the SAME RocksDB storage.
# The CLI consistently works — use subprocess for all SurrealDB operations.

class SurrealDBClient:
    """
    CLI-based SurrealDB client for the Bronze Layer.
    Uses the `surreal sql` subprocess for reliable queries.
    SurrealDB REST API is stateless and returns empty result sets — CLI is our
    trusted communication channel.
    """

    def __init__(self, cli_path: str, endpoint: str, ns: str, db: str, user: str, password: str):
        self.cli_path = cli_path
        self.endpoint = endpoint
        self.ns = ns
        self.db = db
        self.user = user
        self.password = password

    def _run_sql(self, sql: str) -> str:
        """Run a SQL query via `surreal sql` CLI and return raw stdout."""
        cmd = [
            self.cli_path, "sql",
            "-e", self.endpoint,
            "-u", self.user,
            "-p", self.password,
            "--ns", self.ns,
            "--db", self.db,
        ]
        try:
            result = subprocess.run(
                cmd,
                input=sql.encode(),
                capture_output=True,
                timeout=15
            )
            return result.stdout.decode()
        except subprocess.TimeoutExpired:
            log.error("SurrealDB query timed out: %s", sql[:50])
            return "[]"
        except Exception as e:
            log.error("SurrealDB CLI error: %s", e)
            return "[]"

    def insert(self, table: str, data: Dict) -> Optional[str]:
        """
        INSERT a record via CLI. Returns event ID or None.
        SurrealQL JSON objects are embedded as {json_literal} strings in VALUES.
        """
        fields = []
        values = []
        for key, val in data.items():
            fields.append(key)
            if isinstance(val, dict):
                values.append(json.dumps(val))
            elif isinstance(val, str):
                escaped = val.replace("'", "''")
                values.append(f"'{escaped}'")
            else:
                values.append(str(val) if val is not None else "NONE")

        sql = f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({', '.join(values)});\n"
        stdout = self._run_sql(sql)

        # Parse ID from output like [[{ id: events:abc123, ... }]]
        # REST API would give us this directly, but CLI needs parsing
        try:
            match = re.search(r"id:\s*(events:[^\s,}]+)", stdout)
            if match:
                return match.group(1)
        except Exception:
            pass
        return None

    def query(self, sql: str) -> list:
        """Execute a raw SurrealQL query. Returns list of records."""
        stdout = self._run_sql(sql + "\n")
        try:
            # Parse [[{id: events:xxx, ...}, ...]] → list of dicts
            match = re.search(r"\[\[(.*)\]\]", stdout, re.DOTALL)
            if match:
                inner = match.group(1).strip()
                if inner == "" or inner == "NONE":
                    return []
                # Parse each record {key: val, ...}
                records = []
                for rec_match in re.finditer(r"\{([^}]+)\}", inner):
                    fields = rec_match.group(1)
                    rec = {}
                    for field_match in re.finditer(r"(\w+):\s*'([^']*)'", fields):
                        rec[field_match.group(1)] = field_match.group(2)
                    if rec:
                        records.append(rec)
                return records
        except Exception as e:
            log.debug("Query parse error: %s", e)
        return []

    def count(self) -> int:
        """Return total event count."""
        stdout = self._run_sql("SELECT count() FROM events;\n")
        try:
            matches = re.findall(r"count:\s*(\d+)", stdout)
            if matches:
                return sum(int(m) for m in matches)
        except Exception:
            pass
        return 0


# ─── MQTT Bridge ─────────────────────────────────────────────────────────────

class MQTTToSurrealBridge:

    def __init__(self):
        self.mqtt_client: Optional[mqtt.Client] = None
        self.surreal: Optional[SurrealDBClient] = None
        self.running = False
        self._heartbeat_count = 0
        self._msg_count = 0
        self._bridge_event_id: Optional[str] = None

    # ── MQTT Callbacks ──────────────────────────────────────────────────────

    def _on_connect(self, client, userdata, flags, reasonCode, properties=None):
        if reasonCode == 0:
            log.info("✓ Connected to MQTT broker at %s:%s", CFG.mqtt_host, CFG.mqtt_port)
            client.subscribe("#", qos=1)
            log.info("✓ Subscribed to wildcard topic '#' (QoS 1)")
        else:
            log.error("✗ MQTT connection failed — reason code: %s", reasonCode)

    def _on_disconnect(self, client, userdata, reasonCode, properties=None):
        log.warning("⚠ MQTT disconnected (reason %s) — will retry", reasonCode)

    def _on_subscribe(self, client, userdata, mid, reasonCodes, properties=None):
        log.info("✓ Subscription confirmed (mid=%s)", mid)

    def _on_message(self, client, userdata, msg: mqtt.MQTTMessage):
        """Every MQTT message is bridged to SurrealDB Bronze Layer."""
        self._msg_count += 1
        try:
            topic = msg.topic
            raw_payload = msg.payload.decode("utf-8", errors="replace")

            # Parse JSON payload, fallback to raw string
            try:
                payload_data = json.loads(raw_payload)
                is_json = True
            except json.JSONDecodeError:
                payload_data = raw_payload
                is_json = False

            # Extract origin from payload
            origin = CFG.bridge_id
            if isinstance(payload_data, dict):
                origin = (
                    payload_data.get("origin")
                    or payload_data.get("agent")
                    or payload_data.get("service")
                    or payload_data.get("source")
                    or payload_data.get("id")
                    or CFG.bridge_id
                )

            timestamp = datetime.now(timezone.utc).isoformat()

            record = {
                "topic": topic,
                "payload": payload_data,
                "timestamp": timestamp,
                "origin": origin,
                "qos": msg.qos,
                "retain": msg.retain,
                "mid": msg.mid,
                "is_json": is_json,
                "bridge_id": CFG.bridge_id,
            }

            event_id = self.surreal.insert("events", record)
            log.debug(
                "[msg#%s] → topic=%s origin=%s bridge_id=%s",
                self._msg_count, topic, origin, CFG.bridge_id
            )

        except Exception as e:
            log.error("✗ Bridge error for topic '%s': %s", msg.topic, e)

    # ── Heartbeat (self-verification loop) ─────────────────────────────────

    def _publish_heartbeat(self):
        """Publish heartbeat to MQTT — will be bridged back via _on_message."""
        if not CFG.verify_echo or not self.mqtt_client:
            return
        self._heartbeat_count += 1
        heartbeat = {
            "origin": CFG.bridge_id,
            "event_type": "bridge_heartbeat",
            "bridge_id": CFG.bridge_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "heartbeat_number": self._heartbeat_count,
            "total_messages_bridged": self._msg_count,
            "status": "alive",
        }
        topic = f"friday/bridge/{CFG.bridge_id}/heartbeat"
        self.mqtt_client.publish(topic, json.dumps(heartbeat), qos=1)
        log.debug("♥ Heartbeat #%s → %s", self._heartbeat_count, topic)

    # ── Main Loop ────────────────────────────────────────────────────────────

    def start(self):
        log.info("Starting Universal Spine bridge...")

        # ── Connect to SurrealDB via CLI ──────────────────────────────────
        try:
            self.surreal = SurrealDBClient(
                cli_path=CFG.surreal_cli,
                endpoint=CFG.surreal_endpoint,
                ns=CFG.surreal_ns,
                db=CFG.surreal_db,
                user=CFG.surreal_user,
                password=CFG.surreal_pass,
            )
            initial_count = self.surreal.count()
            log.info("✓ Connected to SurrealDB Bronze Layer (endpoint=%s, NS=%s DB=%s)",
                     CFG.surreal_endpoint, CFG.surreal_ns, CFG.surreal_db)
            log.info("✓ Bronze Layer events table accessible (current count: %s)", initial_count)

            # Record the bridge startup event
            bridge_event_id = self.surreal.insert("events", {
                "topic": "friday/bridge/startup",
                "payload": {"event_type": "bridge_started", "bridge_id": CFG.bridge_id},
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "origin": CFG.bridge_id,
                "bridge_id": CFG.bridge_id,
            })
            self._bridge_event_id = bridge_event_id
            log.info("✓ Bridge startup event recorded (id=%s)", bridge_event_id)

        except Exception as e:
            log.critical("✗ Cannot connect to SurrealDB Bronze Layer: %s", e)
            sys.exit(1)

        # ── Connect to MQTT Broker ──────────────────────────────────────────
        client_id = f"mqtt-to-surreal-{uuid.uuid4().hex[:8]}"
        self.mqtt_client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_disconnect = self._on_disconnect
        self.mqtt_client.on_subscribe = self._on_subscribe
        self.mqtt_client.on_message = self._on_message

        try:
            log.info("Connecting to MQTT broker at %s:%s...", CFG.mqtt_host, CFG.mqtt_port)
            self.mqtt_client.connect(CFG.mqtt_host, CFG.mqtt_port, keepalive=CFG.mqtt_keepalive)
            self.mqtt_client.loop_start()
        except Exception as e:
            log.critical("✗ Cannot connect to MQTT broker: %s", e)
            sys.exit(1)

        self.running = True
        log.info("✓ Universal Spine bridge is LIVE")

        # ── Heartbeat + Stats Loop ─────────────────────────────────────────
        last_stats_ts = time.time()
        last_heartbeat_ts = time.time()

        while self.running:
            time.sleep(1)
            now = time.time()

            # Heartbeat interval
            if CFG.heartbeat_interval > 0 and (now - last_heartbeat_ts) >= CFG.heartbeat_interval:
                self._publish_heartbeat()
                last_heartbeat_ts = now

            # Stats log every 60 seconds
            if now - last_stats_ts >= 60:
                event_count = self.surreal.count()
                log.info(
                    "[STATS] messages_bridged=%s heartbeats_sent=%s total_events=%s bridge_id=%s",
                    self._msg_count, self._heartbeat_count, event_count, CFG.bridge_id
                )
                last_stats_ts = now

    def stop(self):
        log.info("Shutting down Universal Spine bridge...")
        self.running = False
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        log.info("Bridge stopped.")


# ─── Entry Point ────────────────────────────────────────────────────────────

def main():
    bridge = MQTTToSurrealBridge()

    def signal_handler(signum, frame):
        log.info("Received signal %s — graceful shutdown...", signum)
        bridge.stop()
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        bridge.start()
    except KeyboardInterrupt:
        bridge.stop()

if __name__ == "__main__":
    main()