# Claude Code — визуальный статус-индикатор для macOS menu bar

Светофор в **строке меню macOS** (menu bar, справа сверху, рядом с часами
и Wi-Fi). Никаких звуков, никакого возврата в терминал — статус всегда на виду:

- 🟢 **idle** — Claude закончил, готов к следующему промпту
- 🟡 **working** — Claude работает над задачей
- 🟠 **waiting** — простаивает и ждёт твоего следующего промпта (`idle_prompt`)
- 🔴 **needs permission** — ждёт твоего разрешения на действие (`permission_prompt`)
- ⚪️ — нет активных сессий Claude Code

Клик по иконке открывает список всех сессий с проектами и их состояниями.
Если открыто несколько сессий, иконка показывает самую «срочную» по
приоритету: 🔴 > 🟠 > 🟡 > 🟢.

## Как это работает

1. Claude Code дёргает хуки на ключевых событиях сессии (`UserPromptSubmit`,
   `Notification`, `Stop`, `SessionStart/End`).
2. Каждый хук — это `notify_status.py`, который пишет JSON-файл со
   статусом в `~/.claude/status/<session_id>.json`.
3. `claude_status_bar.py` — отдельное приложение в menu bar (через
   библиотеку `rumps`), которое раз в ~1.5 сек читает эти файлы и красит
   иконку. Несколько параллельных сессий Claude Code агрегируются:
   если хоть одна ждёт твоего внимания — красный, иначе если хоть одна
   работает — жёлтый, иначе зелёный.

## Установка

### 1. Зависимости

```bash
pip3 install rumps
```

### 2. Хук-скрипт

```bash
mkdir -p ~/.claude/hooks
cp notify_status.py ~/.claude/hooks/notify_status.py
chmod +x ~/.claude/hooks/notify_status.py
```

### 3. Конфиг хуков

Открой (или создай) `~/.claude/settings.json`. Если файла ещё нет —
просто скопируй туда `settings_hooks_snippet.json` целиком. Если файл
уже существует и в нём есть свои хуки или другие настройки — аккуратно
влей секцию `"hooks"` из сниппета в свой JSON (объедини массивы, если
по тем же событиям уже что-то висит, например твой `/housekeeping`).

Проверь, что подхватилось:

```
/hooks
```
внутри Claude Code — должен показать пять новых хуков.

### 4. Меню-бар приложение

Запусти вручную, чтобы проверить, что иконка появляется:

```bash
python3 claude_status_bar.py
```

В строке меню должен появиться ⚪️ (нет активных сессий), который
позеленеет/пожелтеет/покраснеет, когда ты откроешь Claude Code и
начнёшь с ним работать. Клик по иконке — список сессий с проектами.

### 5. Автозапуск при логине (опционально)

```bash
mkdir -p ~/claude-status-bar
cp claude_status_bar.py ~/claude-status-bar/

# подставь реальный путь в plist вместо REPLACE_WITH_FULL_PATH
sed -i '' "s|REPLACE_WITH_FULL_PATH|$HOME/claude-status-bar|" com.claude.statusbar.plist

cp com.claude.statusbar.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.claude.statusbar.plist
```

Чтобы остановить/выгрузить:
```bash
launchctl unload ~/Library/LaunchAgents/com.claude.statusbar.plist
```

## Идеи для доработки

- Заменить эмодзи-кружки на нативные NSImage-иконки (template images),
  если хочется монохромный вид под системную тему.
- PreToolUse/PostToolUse можно тоже завести в notify_status.py, если
  захочешь видеть не просто "working", а конкретно "running tool: Bash"
  во всплывающем меню.
- Если сессии Claude Code иногда падают без SessionEnd — это уже
  покрыто: `STALE_SECONDS` в `claude_status_bar.py` чистит зависшие
  записи через 30 минут без обновлений.
