#!/usr/bin/env bash
set -euo pipefail

# Install Chromium-Fish MCP as a user-scope Claude Code server.
# Run from the repo root. Safe to re-run.

INSTALL_DIR="${CF_INSTALL_DIR:-$HOME/.claude/chromiumfish}"
BIN_DIR="${CF_BIN_DIR:-$HOME/.local/bin}"
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

echo "==> Putting the chromiumfish CLI on PATH for other tools ($BIN_DIR)"
mkdir -p "$BIN_DIR"
ln -sfn "$INSTALL_DIR/venv/bin/chromiumfish" "$BIN_DIR/chromiumfish"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "    warning: $BIN_DIR is not on PATH; add it so other tools can find chromiumfish" ;;
esac

echo "==> Registering with Claude Code (user scope)"
if claude mcp get chromiumfish-web >/dev/null 2>&1; then
  # Keep the existing entry so re-runs don't drop custom env such as CF_PERSONA_SEED.
  echo "    already registered; leaving its config as is"
else
  claude mcp add chromiumfish-web --scope user -- \
    "$INSTALL_DIR/venv/bin/python" "$INSTALL_DIR/mcp/chromiumfish_web.py"
fi

echo "Done. Restart Claude Code to load the new tools."
