# Claude Code — visual status indicator for the macOS menu bar

> Keep an eye on your AI agent without cluttering your workflow.

A traffic light in your **macOS menu bar** (top right, next to the clock and
Wi-Fi). No sounds, no jumping back to the terminal — the status is always in
view:

<img width="299" height="123" alt="image" src="https://github.com/user-attachments/assets/84da231c-b720-4c34-9216-cda6152b7b23" />

- 🟢 **idle** — Claude finished, ready for your next prompt
- 🟡 **working** — Claude is working on a task
- 🟠 **waiting** — idle and waiting for your next prompt (`idle_prompt`)
- 🔴 **needs permission** — waiting for you to approve an action (`permission_prompt`)
- ⚪️ — no active Claude Code sessions

Click the icon to open a list of all sessions with their projects and states.
If several sessions are open, the icon shows the most "urgent" one by priority:
🔴 > 🟠 > 🟡 > 🟢.

## How it works

1. Claude Code fires hooks on key session events (`UserPromptSubmit`,
   `Notification`, `Stop`, `SessionStart/End`).
2. Each hook is `notify_status.py`, which writes a JSON status file to
   `~/.claude/status/<session_id>.json`.
3. `claude_status_bar.py` is a separate menu bar app (using the `rumps`
   library) that reads those files about every 1.5s and colors the icon.
   Multiple parallel Claude Code sessions are aggregated: if any one needs
   your attention the icon is red, otherwise if any is working it's yellow,
   otherwise green.

## Quick install

```bash
./install.sh              # installs deps + hook, wires up settings.json
./install.sh --autostart  # also installs the launch-at-login agent
```

The script checks for macOS and `python3`, installs `rumps`, copies the hook,
and **safely merges** the hooks into your existing `~/.claude/settings.json`
(it backs the file up first and is idempotent — re-running won't duplicate
anything). For the manual steps, see below.

## Manual installation

### 1. Dependencies

```bash
pip3 install rumps
```

### 2. Hook script

```bash
mkdir -p ~/.claude/hooks
cp notify_status.py ~/.claude/hooks/notify_status.py
chmod +x ~/.claude/hooks/notify_status.py
```

### 3. Hook config

Open (or create) `~/.claude/settings.json`. If the file doesn't exist yet,
just copy `settings_hooks_snippet.json` into it as-is. If the file already
exists and has its own hooks or other settings, carefully merge the `"hooks"`
section from the snippet into your JSON (combine the arrays if something is
already bound to the same events, e.g. your own `/housekeeping`).

Verify it was picked up by running:

```
/hooks
```
inside Claude Code — it should show the five new hooks.

### 4. Menu bar app

Run it manually to confirm the icon appears:

```bash
python3 claude_status_bar.py
```

A ⚪️ (no active sessions) should appear in the menu bar, turning
green/yellow/red once you open Claude Code and start working. Click the icon
for the list of sessions and their projects.

### 5. Launch at login (optional)

```bash
mkdir -p ~/claude-status-bar
cp claude_status_bar.py ~/claude-status-bar/

# substitute the real path into the plist instead of REPLACE_WITH_FULL_PATH
sed -i '' "s|REPLACE_WITH_FULL_PATH|$HOME/claude-status-bar|" com.claude.statusbar.plist

cp com.claude.statusbar.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.claude.statusbar.plist
```

To stop/unload:
```bash
launchctl unload ~/Library/LaunchAgents/com.claude.statusbar.plist
```

> **Note:** the plist points at `/usr/local/bin/python3` (Intel Homebrew). On
> Apple Silicon, Python is usually at `/opt/homebrew/bin/python3` — update the
> path in `com.claude.statusbar.plist` accordingly.

## Ideas for improvement

- Replace the emoji circles with native NSImage icons (template images) for a
  monochrome look that follows the system theme.
- `PreToolUse`/`PostToolUse` could also feed into `notify_status.py` if you
  want to see not just "working" but specifically "running tool: Bash" in the
  popup menu.
- If Claude Code sessions sometimes die without `SessionEnd`, that's already
  covered: `STALE_SECONDS` in `claude_status_bar.py` clears stuck entries
  after 30 minutes without updates.

## License

MIT — see [LICENSE](LICENSE).
