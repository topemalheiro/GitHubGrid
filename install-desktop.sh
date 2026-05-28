#!/bin/bash
# Installs GitHubGrid desktop entries for the current user.
# Run this after cloning/moving the repo to its final location.

set -e

SCRIPT_DIR="$(cd "$(dirname "$(realpath "$0")")" && pwd)"
DESKTOP_FILE="$SCRIPT_DIR/github-grid.desktop"

# Generate the real .desktop file with correct paths
sed "s|@INSTALL_DIR@|$SCRIPT_DIR|g" "$SCRIPT_DIR/github-grid.desktop.template" > "$DESKTOP_FILE"

# Install to user applications menu
mkdir -p ~/.local/share/applications
cp "$DESKTOP_FILE" ~/.local/share/applications/

# Install autostart
mkdir -p ~/.config/autostart
cp "$DESKTOP_FILE" ~/.config/autostart/

# Update desktop database
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true

echo "GitHubGrid installed to:"
echo "  ~/.local/share/applications/github-grid.desktop"
echo "  ~/.config/autostart/github-grid.desktop"
echo ""
echo "You can now launch it from the KDE application menu or it will start on next login."
