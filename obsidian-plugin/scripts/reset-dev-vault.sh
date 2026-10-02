#!/usr/bin/env bash
# Reset the development vault to its pristine commit and reinstall a fresh
# aww-retro plugin build. Ignored files survive the reset: plugin data.json
# (AI Providers echo configuration), workspace state, and the plugin build.
#
# Usage: reset-dev-vault.sh [vault-path]   (default: ~/src/aww-dev-vault)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLUGIN_SRC="$REPO_ROOT/obsidian-plugin"
TARGET="${1:-$HOME/src/aww-dev-vault}"

if ! git -C "$TARGET" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: $TARGET is not a git repository" >&2
  exit 1
fi

git -C "$TARGET" reset --hard -q
git -C "$TARGET" clean -fdq

(cd "$PLUGIN_SRC" && npm run build)
PLUGIN_DIR="$TARGET/.obsidian/plugins/aww-retro"
mkdir -p "$PLUGIN_DIR"
cp "$PLUGIN_SRC/manifest.json" "$PLUGIN_SRC/main.js" "$PLUGIN_DIR/"
[[ -f "$PLUGIN_SRC/styles.css" ]] && cp "$PLUGIN_SRC/styles.css" "$PLUGIN_DIR/"

echo "Reset $TARGET to pristine state and reinstalled the aww-retro build."
