#!/usr/bin/env bash
set -euo pipefail

# Install Chromium-Fish MCP as a user-scope Claude Code server.
# Run from the repo root. Safe to re-run.

INSTALL_DIR="${CF_INSTALL_DIR:-$HOME/.claude/chromiumfish}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Creating venv at $INSTALL_DIR/venv"
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install --quiet "chromiumfish[mcp]"

echo "==> Fetching the ChromiumFish browser binary"
"$INSTALL_DIR/venv/bin/chromiumfish" fetch

echo "==> Linking the MCP wrapper into place"
mkdir -p "$INSTALL_DIR/mcp"
ln -sfn "$REPO_DIR/mcp/chromiumfish_web.py" "$INSTALL_DIR/mcp/chromiumfish_web.py"

echo "==> Registering with Claude Code (user scope)"
claude mcp add chromiumfish-web --scope user -- \
  "$INSTALL_DIR/venv/bin/python" "$INSTALL_DIR/mcp/chromiumfish_web.py"

echo "Done. Restart Claude Code to load the new tools."
