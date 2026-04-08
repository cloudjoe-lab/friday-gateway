#!/bin/bash
# Install Friday MQTT Broker as systemd user service
# Run ONCE on Mini PC deployment
# Usage: ./install_service.sh

set -e

MOSQUITTO_SERVICE="/home/krsna/friday-gateway/mqtt/config/mosquitto.service"
SYSTEMD_DIR="$HOME/.config/systemd/user"

echo "Installing Friday MQTT Broker as systemd user service..."

# Create systemd user dir
mkdir -p "$SYSTEMD_DIR"

# Link service file
ln -sf "$MOSQUITTO_SERVICE" "$SYSTEMD_DIR/mosquitto.service"
echo "✓ Service file linked to $SYSTEMD_DIR/mosquitto.service"

# Enable linger (starts service without user logged in)
echo "Note: Run 'loginctl enable-linger' manually if needed:"
echo "  sudo loginctl enable-linger $USER"
echo ""

# Reload systemd, enable and start
systemctl --user daemon-reload
systemctl --user enable --now mosquitto

echo ""
echo "✓ Service installed and started"
systemctl --user status mosquitto --no-pager
