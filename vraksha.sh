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
        docker run -it \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -v "$SCRIPT_DIR/memory:/app/memory" \
            -v "$SCRIPT_DIR/src:/app/src" \
            -v "$SCRIPT_DIR/main.py:/app/main.py" \
            --env-file "$SCRIPT_DIR/$env_file" \
            vraksha
        exit 0
    fi
done

echo "⚠️  No .env file found at $SCRIPT_DIR"
echo "    Add your keys to $SCRIPT_DIR/.env.local"