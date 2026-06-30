#!/usr/bin/env bash
#
# Installer for Claude Code menu bar status indicator.
#
# Usage:
#   ./install.sh              # install hook + deps, print how to run the app
#   ./install.sh --autostart  # also install the launch-at-login agent
#
# Safe to re-run: the settings.json merge is idempotent and backs up the
# existing file before touching it.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
HOOKS_DIR="$CLAUDE_DIR/hooks"
SETTINGS="$CLAUDE_DIR/settings.json"
AUTOSTART=0

[[ "${1:-}" == "--autostart" ]] && AUTOSTART=1

# --- 1. Platform check -------------------------------------------------------
if [[ "$(uname)" != "Darwin" ]]; then
  echo "❌ This app is macOS-only (it lives in the macOS menu bar)." >&2
  exit 1
fi

# --- 2. Python check ---------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ python3 not found." >&2
  echo "   Install it first, e.g.:  brew install python3" >&2
  exit 1
fi
PYTHON="$(command -v python3)"
echo "✅ python3: $PYTHON"

# --- 3. Dependency -----------------------------------------------------------
echo "→ Installing rumps…"
"$PYTHON" -m pip install --user --quiet rumps
echo "✅ rumps installed"

# --- 4. Hook script ----------------------------------------------------------
mkdir -p "$HOOKS_DIR"
cp "$REPO_DIR/notify_status.py" "$HOOKS_DIR/notify_status.py"
chmod +x "$HOOKS_DIR/notify_status.py"
echo "✅ hook copied to $HOOKS_DIR/notify_status.py"

# --- 5. Merge hooks into settings.json (idempotent, with backup) -------------
echo "→ Merging hooks into $SETTINGS…"
"$PYTHON" - "$SETTINGS" "$REPO_DIR/settings_hooks_snippet.json" <<'PY'
import json, sys, pathlib, shutil, time

settings_path = pathlib.Path(sys.argv[1])
snippet_path = pathlib.Path(sys.argv[2])

snippet = json.loads(snippet_path.read_text())["hooks"]

if settings_path.exists():
    backup = settings_path.with_suffix(f".json.bak.{int(time.time())}")
    shutil.copy2(settings_path, backup)
    print(f"   backed up existing settings to {backup.name}")
    settings = json.loads(settings_path.read_text() or "{}")
else:
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings = {}

hooks = settings.setdefault("hooks", {})

def has_notify(groups):
    for g in groups:
        for h in g.get("hooks", []):
            if "notify_status.py" in h.get("command", ""):
                return True
    return False

added = 0
for event, groups in snippet.items():
    existing = hooks.setdefault(event, [])
    if has_notify(existing):
        continue          # already wired up for this event
    existing.extend(groups)
    added += 1

settings_path.write_text(json.dumps(settings, indent=2) + "\n")
print(f"✅ settings.json updated ({added} event(s) added, "
      f"{len(snippet) - added} already present)")
PY

# --- 6. Optional launch-at-login agent --------------------------------------
if [[ "$AUTOSTART" == "1" ]]; then
  echo "→ Setting up launch-at-login agent…"
  APP_DIR="$HOME/claude-status-bar"
  mkdir -p "$APP_DIR"
  cp "$REPO_DIR/claude_status_bar.py" "$APP_DIR/"

  PLIST="$HOME/Library/LaunchAgents/com.claude.statusbar.plist"
  sed -e "s|REPLACE_WITH_FULL_PATH|$APP_DIR|" \
      -e "s|/usr/local/bin/python3|$PYTHON|" \
      "$REPO_DIR/com.claude.statusbar.plist" > "$PLIST"

  launchctl unload "$PLIST" 2>/dev/null || true
  launchctl load "$PLIST"
  echo "✅ launch agent installed and started ($PLIST)"
  echo "   To stop:  launchctl unload $PLIST"
else
  echo
  echo "Run the menu bar app with:"
  echo "    python3 $REPO_DIR/claude_status_bar.py"
  echo "(or re-run with --autostart to launch it automatically at login)"
fi

echo
echo "Done. Open Claude Code and watch the menu bar light up. 🚦"
