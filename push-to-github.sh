#!/bin/bash
# push-to-github.sh — Push Friday Gateway to GitHub
# Run this on your CPU when you have your GitHub token available.
#
# Usage: ./push-to-github.sh
#   or with token: GITHUB_TOKEN=ghp_xxx ./push-to-github.sh

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_NAME="friday-gateway"
GITHUB_USER="${GITHUB_USER:-}"  # Set this if different from token default

cd "$REPO_DIR"

echo "============================================"
echo "  Friday Gateway → GitHub Push Script"
echo "============================================"
echo ""

# ─── Step 1: Find GitHub Token ────────────────────────────────
TOKEN="${GITHUB_TOKEN:-}"

if [ -z "$TOKEN" ]; then
    # Try gh CLI
    if command -v gh &>/dev/null && gh auth status &>/dev/null; then
        echo "[1/4] Using gh CLI credentials..."
        USE_GH=1
    else
        echo "[1/4] No token found. Options:"
        echo "  a) Export GITHUB_TOKEN env var:  export GITHUB_TOKEN=ghp_xxx"
        echo "  b) Install & auth gh:           sudo apt install gh && gh auth login"
        echo "  c) Enter token now (PAT):       "
        read -r -s -p "  GitHub Token: " TOKEN
        echo ""
    fi
fi

if [ -z "$TOKEN" ] && [ "${USE_GH:-0}" != "1" ]; then
    echo "ERROR: No GitHub credentials available. Aborting."
    exit 1
fi

# ─── Step 2: Get GitHub Username ──────────────────────────────
if [ "${USE_GH:-0}" == "1" ]; then
    GITHUB_USER=$(gh api user --jq .login 2>/dev/null)
    echo "[2/4] GitHub user: $GITHUB_USER"
else
    GITHUB_USER=$(curl -s -H "Authorization: Bearer $TOKEN" \
        https://api.github.com/user --jq .login 2>/dev/null)
    echo "[2/4] GitHub user: $GITHUB_USER"
fi

if [ -z "$GITHUB_USER" ]; then
    echo "ERROR: Could not determine GitHub username. Check your token."
    exit 1
fi

# ─── Step 3: Create GitHub Repo ───────────────────────────────
echo "[3/4] Creating GitHub repository '$REPO_NAME'..."

if [ "${USE_GH:-0}" == "1" ]; then
    gh repo create "$REPO_NAME" --public --source=. --push 2>/dev/null && echo "  ✓ Repo created and pushed!" || {
        # Try push only if repo already exists
        git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git" 2>/dev/null || true
        git branch -M main
        git push -u origin main 2>/dev/null && echo "  ✓ Pushed to existing repo!" || echo "  ! Repo may already exist — check https://github.com/$GITHUB_USER/$REPO_NAME"
    }
else
    # Use GitHub API
    RESPONSE=$(curl -s -X POST \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"$REPO_NAME\",\"public\":true,\"auto_init\":false}" \
        "https://api.github.com/user/repos" 2>/dev/null)
    
    if echo "$RESPONSE" | grep -q '"full_name"'; then
        echo "  ✓ Repository created!"
    elif echo "$RESPONSE" | grep -q '"Already exists"'; then
        echo "  ! Repository already exists — pushing to it"
    else
        echo "  ! Repo creation response: $RESPONSE" 
    fi
    
    # Set remote and push
    git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git" 2>/dev/null || {
        git remote set-url origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
    }
    git branch -M main
    git push -u origin main
    echo "  ✓ Pushed to https://github.com/$GITHUB_USER/$REPO_NAME"
fi

echo ""
echo "============================================"
echo "  ✓ Friday Gateway is live on GitHub!"
echo "============================================"
