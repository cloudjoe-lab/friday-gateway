#!/usr/bin/env bash
# =============================================================================
# Paperclip Setup — Native (no Docker)
# =============================================================================
# Installs pnpm, clones Paperclip, installs deps, enables systemd service.
# Run once. Safe to re-run.
# =============================================================================

set -euo pipefail

PAPERCLIP_HOME="${PAPERCLIP_HOME:-/home/krsna/paperclip}"
PAPERCLIP_SYSTEMD_HOME="/home/krsna/.config/systemd/user"

echo "==> Checking prerequisites"

# Node 20+ required
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    echo "ERROR: Node 20+ required. Found: $(node --version)"
    exit 1
fi
echo "    Node $(node --version) ✓"

# pnpm — installed to ~/.local/bin (npm global prefix)
export PATH="$HOME/.local/bin:$PATH"
if ! command -v pnpm &>/dev/null; then
    echo "==> Installing pnpm to ~/.local/bin..."
    mkdir -p "$HOME/.local"
    npm install -g pnpm --prefix "$HOME/.local"
fi
echo "    pnpm $(pnpm --version) ✓"

# =============================================================================
# Clone / update Paperclip
# =============================================================================
if [ -d "$PAPERCLIP_HOME/.git" ]; then
    echo "==> Updating Paperclip at $PAPERCLIP_HOME"
    cd "$PAPERCLIP_HOME" && git pull
else
    echo "==> Cloning Paperclip to $PAPERCLIP_HOME"
    git clone https://github.com/paperclipai/paperclip.git "$PAPERCLIP_HOME"
fi

# =============================================================================
# Install deps
# =============================================================================
echo "==> Installing Paperclip dependencies"
cd "$PAPERCLIP_HOME" && pnpm install

# =============================================================================
# Install systemd service
# =============================================================================
echo "==> Installing systemd service"
mkdir -p "$PAPERCLIP_SYSTEMD_HOME"

# Copy service file if different from what's already there
SERVICE_FILE="$PAPERCLIP_SYSTEMD_HOME/paperclip.service"
cat > "$SERVICE_FILE" << 'EOF'
[Unit]
Description=Paperclip — AI Company Control Plane
After=network.target
StartLimitIntervalSec=600
StartLimitBurst=5

[Service]
Type=simple
ExecStartPre=/bin/sleep 2
ExecStart=/home/krsna/.local/bin/pnpm dev:once
WorkingDirectory=/home/krsna/paperclip
Environment="PATH=/home/krsna/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PAPERCLIP_HOME=/home/krsna/.paperclip"
Restart=on-failure
RestartSec=30
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=60
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

echo "    Service installed: $SERVICE_FILE"

# Reload systemd, enable and start
systemctl --user daemon-reload
systemctl --user enable paperclip.service

echo ""
echo "==> Paperclip is ready!"
echo ""
echo "  To start now:     systemctl --user start paperclip"
echo "  To check status: systemctl --user status paperclip"
echo "  To view logs:    journalctl --user -u paperclip -f"
echo "  To stop:         systemctl --user stop paperclip"
echo ""
echo "  Then open:       http://localhost:3100"
echo ""
