#!/bin/bash

set -e

REPO="https://github.com/vraksha/vraksha"
INSTALL_DIR="$HOME/.vraksha"
INSTALL_PATH="/usr/local/bin/vraksha"

echo "Installing Vraksha..."

# Clone or update repo
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    git -C "$INSTALL_DIR" pull
else
    echo "Cloning Vraksha..."
    git clone "$REPO" "$INSTALL_DIR"
fi

# Create symlink
sudo ln -sf "$INSTALL_DIR/vraksha.sh" "$INSTALL_PATH"
sudo chmod +x "$INSTALL_PATH"

# Setup env file if not exists
if [ ! -f "$INSTALL_DIR/.env.local" ]; then
    cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env.local"
    echo ""
    echo "⚠️  Add your API keys to $INSTALL_DIR/.env.local"
    echo "    nano $INSTALL_DIR/.env.local"
fi

echo "Building Vraksha Docker image (this may take a minute)..."
docker build -t vraksha "$INSTALL_DIR"


echo ""
echo "Vraksha installed! Run 'vraksha' from anywhere."
