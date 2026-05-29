#!/bin/bash

set -e

REPO="https://github.com/vraksha/vraksha"
INSTALL_DIR="$HOME/.vraksha"
INSTALL_PATH="/usr/local/bin/vraksha"

if [ "$(uname -s 2>/dev/null)" != "Darwin" ]; then
    echo "This installer is for macOS. Use install-linux.sh on Linux or install-wsl.sh inside WSL."
    exit 1
fi

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Missing required command: $1"
        exit 1
    fi
}

start_docker_if_possible() {
    if docker info >/dev/null 2>&1; then
        return 0
    fi

    if command -v open >/dev/null 2>&1; then
        echo "Starting Docker Desktop..."
        open -gj -a Docker >/dev/null 2>&1 || open -a Docker >/dev/null 2>&1 || true
    fi

    attempts=0
    while [ "$attempts" -lt 30 ]; do
        if docker info >/dev/null 2>&1; then
            return 0
        fi
        sleep 2
        attempts=$((attempts + 1))
    done

    return 1
}

ensure_docker_ready() {
    if start_docker_if_possible; then
        return 0
    fi

    echo "Docker is not running. Start Docker Desktop, wait until it is ready, then rerun install-macos.sh."
    exit 1
}

echo "Installing Vraksha for macOS..."

require_command git
require_command docker

if ! docker compose version >/dev/null 2>&1; then
    echo "Docker Compose is required: install Docker Desktop."
    exit 1
fi

ensure_docker_ready

if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    git -C "$INSTALL_DIR" pull
else
    echo "Cloning Vraksha..."
    git clone "$REPO" "$INSTALL_DIR"
fi

sudo mkdir -p "$(dirname "$INSTALL_PATH")"
sudo ln -sf "$INSTALL_DIR/vraksha.sh" "$INSTALL_PATH"
sudo chmod +x "$INSTALL_PATH"

if [ ! -f "$INSTALL_DIR/.env.local" ]; then
    cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env.local"
    echo ""
    echo "Add your API keys to $INSTALL_DIR/.env.local"
    echo "nano $INSTALL_DIR/.env.local"
fi

echo "Building Vraksha Docker image (this may take a minute)..."
docker build -t vraksha-runtime "$INSTALL_DIR"

echo ""
echo "Vraksha installed! Run 'vraksha' from anywhere."
