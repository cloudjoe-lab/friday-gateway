#!/bin/bash
# Start Friday MQTT Broker
# Phase 3.1.2 — Central Data Hub
# Usage: ./start_broker.sh

export LD_LIBRARY_PATH=/home/krsna/.local/lib:$LD_LIBRARY_PATH
export MQTT_HOST=127.0.0.1
export MQTT_PORT=1883

MOSQUITTO_BIN="/home/krsna/.local/bin/mosquitto"
CONF="/home/krsna/friday-gateway/mqtt/config/mosquitto.conf"
DATA_DIR="/home/krsna/friday-gateway/mqtt/data"
LOG_DIR="/home/krsna/friday-gateway/mqtt/logs"
PIDFILE="/home/krsna/friday-gateway/mqtt/mosquitto.pid"

mkdir -p "$DATA_DIR" "$LOG_DIR"

echo "Starting Friday MQTT Broker..."
$MOSQUITTO_BIN -c "$CONF" -d -pid "$PIDFILE"

if [ $? -eq 0 ]; then
    echo "✓ Broker started (PID: $(cat $PIDFILE))"
    echo "  Listening on: $MQTT_HOST:$MQTT_PORT"
    echo "  WebSocket: $MQTT_HOST:9001"
else
    echo "✗ Failed to start broker"
    exit 1
fi
