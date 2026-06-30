#!/usr/bin/env python3
"""
Claude Code status bar indicator (macOS menu bar).

Установка:
    pip3 install rumps
    python3 claude_status_bar.py

Иконка в menu bar показывает агрегированный статус всех активных
сессий Claude Code (по приоритету: attention > waiting > working > idle).
Клик по иконке открывает список сессий с проектами и их состоянием.

Для автозапуска при логине см. com.claude.statusbar.plist рядом.
"""
import json
import pathlib
import time

import rumps

STATUS_DIR = pathlib.Path.home() / ".claude" / "status"
STALE_SECONDS = 60 * 30  # сессии без обновлений дольше 30 мин считаем мёртвыми
REFRESH_SECONDS = 1.5

ICONS = {
    "attention": "🔴",
    "waiting": "🟠",
    "working": "🟡",
    "idle": "🟢",
    "none": "⚪️",
}

STATE_LABELS = {
    "attention": "needs permission",
    "waiting": "ready for your prompt",
    "working": "working",
    "idle": "idle",
}

# Порядок убывания приоритета для агрегации между сессиями.
PRIORITY = ["attention", "waiting", "working", "idle"]


class ClaudeStatusApp(rumps.App):
    def __init__(self):
        super().__init__("Claude", title=ICONS["none"], quit_button="Quit")
        self.timer = rumps.Timer(self.refresh, REFRESH_SECONDS)
        self.timer.start()
        self.refresh(None)

    def read_sessions(self):
        STATUS_DIR.mkdir(parents=True, exist_ok=True)
        now = time.time()
        sessions = []
        for f in STATUS_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text())
            except Exception:
                continue
            ts = data.get("ts", 0)
            if now - ts > STALE_SECONDS:
                f.unlink(missing_ok=True)
                continue
            sessions.append(data)
        return sessions

    def refresh(self, _):
        sessions = self.read_sessions()
        now = time.time()

        if not sessions:
            overall = "none"
        else:
            states = {s.get("state") for s in sessions}
            overall = next((p for p in PRIORITY if p in states), "idle")

        self.title = ICONS[overall]

        self.menu.clear()
        if not sessions:
            self.menu.add(rumps.MenuItem("No active Claude Code sessions"))
        else:
            sessions.sort(key=lambda s: -s.get("ts", 0))
            for s in sessions:
                icon = ICONS.get(s.get("state"), ICONS["none"])
                label = STATE_LABELS.get(s.get("state"), s.get("state", "?"))
                age = int(now - s.get("ts", now))
                project = s.get("project", "unknown")
                self.menu.add(
                    rumps.MenuItem(f"{icon} {project} — {label} ({age}s ago)")
                )
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Refresh now", callback=self.refresh))


if __name__ == "__main__":
    ClaudeStatusApp().run()
