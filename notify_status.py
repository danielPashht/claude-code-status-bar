#!/usr/bin/env python3
"""
Hook script for Claude Code -> записывает статус текущей сессии в файл,
который потом читает меню-бар приложение (claude_status_bar.py).

Использование (вызывается из ~/.claude/settings.json):
    python3 notify_status.py <state>
где <state> одно из: idle | working | end | notify

Для "notify" (хук Notification) конкретное состояние выбирается по полю
notification_type из payload:
    permission_prompt -> attention (🔴, нужно разрешение)
    idle_prompt       -> waiting   (🟠, ждёт твоего следующего промпта)
    остальные типы    -> игнорируются (статус не меняется)

Состояние сессии хранится в ~/.claude/status/<session_id>.json
"""
import sys
import json
import time
import pathlib

STATUS_DIR = pathlib.Path.home() / ".claude" / "status"


def main():
    if len(sys.argv) < 2:
        sys.exit(0)  # тихо выходим, чтобы не ломать хук-цепочку Claude Code

    state = sys.argv[1]

    # JSON прилетает на stdin от Claude Code (session_id, cwd и т.д.)
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    session_id = data.get("session_id", "unknown")
    cwd = data.get("cwd", "")
    project = pathlib.Path(cwd).name if cwd else "unknown"

    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    session_file = STATUS_DIR / f"{session_id}.json"

    if state == "end":
        session_file.unlink(missing_ok=True)
        return

    # Хук Notification приходит с общим state="notify"; реальное состояние
    # выбираем по типу уведомления (есть в payload, см. docs по хукам).
    if state == "notify":
        ntype = data.get("notification_type", "")
        if ntype == "permission_prompt":
            state = "attention"   # реально нужно разрешение -> 🔴
        elif ntype == "idle_prompt":
            state = "waiting"     # просто ждёт следующего промпта -> 🟠
        else:
            # auth_success / elicitation_* и т.п. — не трогаем текущий статус
            return

    payload = {
        "state": state,       # idle | working | attention | waiting
        "project": project,
        "cwd": cwd,
        "ts": time.time(),
    }
    session_file.write_text(json.dumps(payload))


if __name__ == "__main__":
    main()
