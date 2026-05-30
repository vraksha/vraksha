#!/bin/bash

set -e

REPO="https://github.com/vraksha/vraksha"
INSTALL_DIR="$HOME/.vraksha"
INSTALL_PATH="/usr/local/bin/vraksha"

if [ "$(uname -s 2>/dev/null)" != "Linux" ]; then
    echo "This installer is for Linux. Use install-macos.sh on macOS or install-wsl.sh inside WSL."
    exit 1
fi

if grep -qiE "microsoft|wsl" /proc/version 2>/dev/null; then
    echo "This looks like WSL. Use install-wsl.sh instead."
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

    if command -v systemctl >/dev/null 2>&1 && systemctl is-system-running >/dev/null 2>&1; then
        if ! systemctl is-active --quiet docker; then
            echo "Starting Docker service..."
            sudo systemctl start docker
        fi
    elif command -v service >/dev/null 2>&1 && [ -x /etc/init.d/docker ]; then
        if ! service docker status >/dev/null 2>&1; then
            echo "Starting Docker service..."
            sudo service docker start
        fi
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

    docker_error="$(docker info 2>&1 || true)"
    if printf "%s" "$docker_error" | grep -qi "permission denied"; then
        if command -v usermod >/dev/null 2>&1; then
            echo "Docker permission denied. Adding $USER to the docker group..."
            sudo usermod -aG docker "$USER"
            echo "Please run: newgrp docker then rerun install-linux.sh"
            exit 1
        fi
    fi

    echo "Docker is not running. Start the Docker daemon, then rerun install-linux.sh."
    exit 1
}

echo "Installing Vraksha for Linux..."

require_command git
require_command docker

if ! docker compose version >/dev/null 2>&1; then
    echo "Docker Compose is required: install the Docker Compose plugin."
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
