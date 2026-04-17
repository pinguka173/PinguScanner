#!/bin/bash

REPO_URL="https://github.com/pinguka173/PinguScanner"
INSTALL_DIR="/opt/pinguscan"
BIN_SYMLINK="/usr/local/bin/pinguscan"
ENTRY_SCRIPT="run.sh"  # the launcher wrapper

set -e

echo "[*] Cloning the repo from $REPO_URL..."
sudo git clone "$REPO_URL" "$INSTALL_DIR"

echo "[*] Setting permissions..."
sudo chmod -R +x "$INSTALL_DIR"

echo "[*] Creating launcher wrapper..."
sudo tee "$INSTALL_DIR/$ENTRY_SCRIPT" > /dev/null <<EOF
#!/bin/bash
python3 "$INSTALL_DIR/main.py" "\$@"
EOF
sudo chmod +x "$INSTALL_DIR/$ENTRY_SCRIPT"

echo "[*] Linking to global command: $BIN_SYMLINK"
sudo ln -sf "$INSTALL_DIR/$ENTRY_SCRIPT" "$BIN_SYMLINK"

echo "[+] Installed. Now type 'pinguscan --help' to play king penguin."
