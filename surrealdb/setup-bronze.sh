#!/bin/bash
#
# SurrealDB Bronze Layer Schema
# CQRS Event Store for Hermes Gateway
#

ENDPOINT="${SURREAL_ENDPOINT:-http://localhost:8080}"
USER="${SURREAL_USER:-root}"
PASS="${SURREAL_PASS:-root}"
NS="main"
DB="main"

echo "[Bronze Schema] Setting up CQRS event store on $ENDPOINT..."

# Define the events table (schemaless for flexibility)
curl -s -X POST "$ENDPOINT/sql" \
  -H "Content-Type: application/json" \
  -u "$USER:$PASS" \
  -d "{\"ns\":\"$NS\",\"db\":\"$DB\",\"sql\":\"DEFINE TABLE IF NOT EXISTS events SCHEMAFULL;\"}" > /dev/null

# Define indexes for high-performance stream reads
echo "[Bronze Schema] Creating stream indexes..."
curl -s -X POST "$ENDPOINT/sql" \
  -H "Content-Type: application/json" \
  -u "$USER:$PASS" \
  -d "{\"ns\":\"$NS\",\"db\":\"$DB\",\"sql\":\"DEFINE INDEX IF NOT EXISTS events_stream ON events FIELDS stream;\"}" > /dev/null

curl -s -X POST "$ENDPOINT/sql" \
  -H "Content-Type: application/json" \
  -u "$USER:$PASS" \
  -d "{\"ns\":\"$NS\",\"db\":\"$DB\",\"sql\":\"DEFINE INDEX IF NOT EXISTS events_stream_seq ON events FIELDS stream, sequence;\"}" > /dev/null

curl -s -X POST "$ENDPOINT/sql" \
  -H "Content-Type: application/json" \
  -u "$USER:$PASS" \
  -d "{\"ns\":\"$NS\",\"db\":\"$DB\",\"sql\":\"DEFINE INDEX IF NOT EXISTS events_type ON events FIELDS event_type;\"}" > /dev/null

curl -s -X POST "$ENDPOINT/sql" \
  -H "Content-Type: application/json" \
  -u "$USER:$PASS" \
  -d "{\"ns\":\"$NS\",\"db\":\"$DB\",\"sql\":\"DEFINE INDEX IF NOT EXISTS events_occurred ON events FIELDS occurred_at;\"}" > /dev/null

echo "[Bronze Schema] ✓ Indexes created"

# Insert bootstrap events
echo "[Bronze Schema] Inserting bootstrap events..."
curl -s -X POST "$ENDPOINT/sql" \
  -H "Content-Type: application/json" \
  -u "$USER:$PASS" \
  -d "{\"ns\":\"$NS\",\"db\":\"$DB\",\"sql\":\"INSERT INTO events (stream, sequence, version, event_type, payload) VALUES ('gateway', 1, 1, 'BronzeLayerInitialized', {version:'3.0.5', engine:'rocksdb', port:$PORT});\"}" > /dev/null

echo "[Bronze Schema] ✓ Schema complete"
echo ""
echo "Available streams:"
curl -s -X POST "$ENDPOINT/sql" \
  -H "Content-Type: application/json" \
  -u "$USER:$PASS" \
  -d "{\"ns\":\"$NS\",\"db\":\"$DB\",\"sql\":\"SELECT stream, count() AS count FROM events GROUP BY stream;\"}" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); [print(f'  {r[\"stream\"]}: {r[\"count\"]} events') for r in d[0].get('result',{}).get('value',{}).get('([])',[])]" 2>/dev/null || echo "  (run queries to populate)"