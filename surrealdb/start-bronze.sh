#!/bin/bash
#
# SurrealDB Bronze Layer - Startup Script
# Stores Hermes Gateway event streams in RocksDB
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BINARY="$SCRIPT_DIR/surreal"
DATA_DIR="$SCRIPT_DIR/bronze"
PORT="${SURREAL_PORT:-8080}"
USER="${SURREAL_USER:-root}"
PASS="${SURREAL_PASS:-root}"
LOG_DIR="$SCRIPT_DIR/logs"

# Ensure data directory exists
mkdir -p "$DATA_DIR" "$LOG_DIR"

# Check if already running
if ss -tlnp 2>/dev/null | grep -q ":${PORT} "; then
    echo "[SurrealDB] Already running on port $PORT"
    exit 0
fi

# Launch in background
echo "[SurrealDB] Starting Bronze Layer on port $PORT..."
cd "$SCRIPT_DIR"
nohup ./surreal start \
    -b "0.0.0.0:$PORT" \
    -u "$USER" \
    -p "$PASS" \
    "rocksdb:///home/krsna/friday-gateway/surrealdb/bronze" \
    --log info \
    > "$LOG_DIR/surrealdb.log" 2>&1 &

echo "[SurrealDB] PID: $!"
sleep 2

# Verify
if ss -tlnp | grep -q ":${PORT} "; then
    echo "[SurrealDB] ✓ Running on 0.0.0.0:$PORT"
else
    echo "[SurrealDB] ✗ Failed to start. Check $LOG_DIR/surrealdb.log"
    exit 1
fi