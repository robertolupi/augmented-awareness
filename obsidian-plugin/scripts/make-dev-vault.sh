#!/usr/bin/env bash
# Create a disposable, git-tracked development vault seeded from demo_vault.
# The pristine state (seed + aww-retro plugin installed and enabled) is the
# initial commit, so `git reset --hard && git clean -fd` restores it —
# see reset-dev-vault.sh.
#
# Usage: make-dev-vault.sh [target-path]   (default: ~/src/aww-dev-vault)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SEED="$REPO_ROOT/demo_vault/demo_vault"
PLUGIN_SRC="$REPO_ROOT/obsidian-plugin"
TARGET="${1:-$HOME/src/aww-dev-vault}"

if [[ -e "$TARGET" && -n "$(ls -A "$TARGET" 2>/dev/null)" ]]; then
  echo "error: $TARGET exists and is not empty" >&2
  exit 1
fi

if [[ ! -f "$PLUGIN_SRC/main.js" ]]; then
  (cd "$PLUGIN_SRC" && npm run build)
fi

mkdir -p "$TARGET"
cp -R "$SEED/" "$TARGET/"

# Install the aww-retro plugin build.
PLUGIN_DIR="$TARGET/.obsidian/plugins/aww-retro"
mkdir -p "$PLUGIN_DIR"
cp "$PLUGIN_SRC/manifest.json" "$PLUGIN_SRC/main.js" "$PLUGIN_DIR/"
[[ -f "$PLUGIN_SRC/styles.css" ]] && cp "$PLUGIN_SRC/styles.css" "$PLUGIN_DIR/"

# Enable the plugin in the copy (the demo_vault seed stays unchanged).
python3 - "$TARGET/.obsidian/community-plugins.json" <<'EOF'
import json, sys
p = sys.argv[1]
plugins = json.load(open(p))
if "aww-retro" not in plugins:
    plugins.append("aww-retro")
json.dump(plugins, open(p, "w"), indent=2)
EOF

cat > "$TARGET/.gitignore" <<'EOF'
.DS_Store
.trash/
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/workspace/
.obsidian/cache/
# Plugin build output — reinstall via obsidian-plugin/scripts/.
.obsidian/plugins/aww-retro/main.js
# Plugin settings may contain provider credentials (e.g. ai-providers).
.obsidian/plugins/*/data.json
EOF

git -C "$TARGET" init -q
git -C "$TARGET" add -A
git -C "$TARGET" commit -qm "Pristine demo-seeded development vault"
echo "Created $TARGET (git repo, pristine commit $(git -C "$TARGET" rev-parse --short HEAD))."
