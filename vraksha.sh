#!/bin/bash

INSTALL_PATH="/usr/local/bin/vraksha"
SCRIPT_PATH="$(realpath "$0")"
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")

# Self-install if not already installed
if [ "$SCRIPT_PATH" != "$INSTALL_PATH" ] && [ ! -L "$INSTALL_PATH" ]; then
    echo "Setting up vraksha command..."
    sudo ln -sf "$SCRIPT_PATH" "$INSTALL_PATH"
    sudo chmod +x "$INSTALL_PATH"
    echo "Done! You can now run 'vraksha' from anywhere."
    echo ""
fi

for env_file in .env.local .env.example .env .env.production .env.development; do
    if [ -f "$SCRIPT_DIR/$env_file" ]; then
        docker compose -f "$SCRIPT_DIR/docker-compose.yml" --env-file "$SCRIPT_DIR/$env_file" up --build
        exit 0
    fi
done

echo "⚠️  No .env file found at $SCRIPT_DIR"
echo "    Add your keys to $SCRIPT_DIR/.env.local"