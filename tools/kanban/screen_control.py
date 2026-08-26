#!/usr/bin/env python3
"""Screen control via AppleScript — websites + specific apps.

Exports `execute(command, params)` for the kanban server.
Commands: open_url, click_at, type_text, key_press, screenshot,
open_app, close_app, get_frontmost_app, scroll, drag, applescript.
"""
import subprocess
import base64
import logging
import shlex
from pathlib import Path

logger = logging.getLogger(__name__)

SCREENSHOT_PATH = Path("/tmp/hermes_screen.png")
ALLOWED_APPS = {
    "Safari", "Google Chrome", "Chrome", "Firefox", "Arc", "Brave Browser",
    "Finder", "Terminal", "iTerm2", "Code", "Visual Studio Code",
    "Notes", "TextEdit", "Mail", "Messages", "Slack", "Telegram",
    "Notion", "Obsidian", "Figma", "Linear", "GitHub Desktop",
    "Spotify", "Music", "Photos", "Preview", "Calculator",
    "System Preferences", "System Settings", "Activity Monitor",
    "Comet", "Zen", "Warp",
}


def run_applescript(script: str, timeout: int = 30) -> dict:
    """Run an AppleScript and return {ok, output, error}."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "ok": result.returncode == 0,
            "output": result.stdout.strip(),
            "error": result.stderr.strip() if result.returncode != 0 else "",
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"AppleScript timed out after {timeout}s"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def open_url(url: str) -> dict:
    """Open a URL in the default browser."""
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url
    script = f'open location "{url}"'
    return run_applescript(script)


def click_at(x: int, y: int) -> dict:
    """Click at absolute screen coordinates."""
    script = f'''
    do shell script "cliclick c:{x},{y}" 2>/dev/null
    if result is missing value then
        return "clicked {x},{y}"
    else
        return result as string
    end if
    '''
    result = run_applescript(script)
    if not result["ok"] or "missing value" in str(result.get("output", "")):
        script2 = f'''
        tell application "System Events"
            click at {{{x}, {y}}}
        end tell
        '''
        return run_applescript(script2)
    return result


def type_text(text: str) -> dict:
    """Type text into the currently focused field."""
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    script = f'''
    tell application "System Events"
        keystroke "{escaped}"
    end tell
    '''
    return run_applescript(script)


def key_press(keys: str) -> dict:
    """Press a keyboard shortcut like 'cmd+l', 'cmd+shift+4', 'return'."""
    parts = [p.strip().lower() for p in keys.split("+")]
    modifiers = {"cmd": "command down", "ctrl": "control down",
                 "opt": "option down", "shift": "shift down",
                 "alt": "option down"}
    key = parts[-1]
    mod_parts = [modifiers.get(p, p + " down") for p in parts[:-1]]
    mod_str = ", ".join(mod_parts) if mod_parts else ""
    if mod_str:
        script = f'''
        tell application "System Events"
            key code (key code of "{key}")
        end tell
        '''
        script = f'''
        tell application "System Events"
            keystroke "{key}" using {{"{'", "'.join(p for p in parts[:-1])}"}}
        end tell
        '''
    else:
        script = f'''
        tell application "System Events"
            keystroke "{key}"
        end tell
        '''
    return run_applescript(script)


def screenshot() -> dict:
    """Capture the screen and return as base64 PNG."""
    try:
        subprocess.run(["screencapture", "-x", "-C", str(SCREENSHOT_PATH)],
                       check=True, timeout=10)
        data = SCREENSHOT_PATH.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        return {"ok": True, "image": b64, "format": "png",
                "size_bytes": len(data)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def open_app(name: str) -> dict:
    """Open or focus an app by name."""
    if name not in ALLOWED_APPS:
        return {"ok": False, "error": f"App '{name}' not in allowlist"}
    script = f'''
    tell application "{name}"
        activate
    end tell
    '''
    return run_applescript(script)


def close_app(name: str) -> dict:
    """Quit an app by name."""
    if name not in ALLOWED_APPS:
        return {"ok": False, "error": f"App '{name}' not in allowlist"}
    script = f'''
    tell application "{name}"
        quit
    end tell
    '''
    return run_applescript(script)


def get_frontmost_app() -> dict:
    """Get the name of the frontmost app."""
    script = '''
    tell application "System Events"
        name of first application process whose frontmost is true
    end tell
    '''
    result = run_applescript(script)
    if result["ok"]:
        result["app"] = result["output"]
    return result


def scroll(direction: str, amount: int = 5) -> dict:
    """Scroll up or down."""
    key = {"up": 125, "down": 119}.get(direction)
    if key is None:
        return {"ok": False, "error": "direction must be 'up' or 'down'"}
    script = f'''
    tell application "System Events"
        repeat {amount} times
            key code {key}
        end repeat
    end tell
    '''
    return run_applescript(script)


def drag(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Drag from one point to another (basic, via shell)."""
    script = f'''
    do shell script "cliclick m:{x1},{y1} d:{x2},{y2}" 2>/dev/null
    '''
    return run_applescript(script)


def raw_applescript(script: str) -> dict:
    """Run raw AppleScript — caller is responsible for safety."""
    return run_applescript(script)


def execute(command: str, params: dict = None) -> dict:
    """Dispatch a screen control command."""
    params = params or {}
    logger.info(f"screen_control: {command} {params}")
    dispatch = {
        "open_url": lambda: open_url(params.get("url", "")),
        "click_at": lambda: click_at(int(params.get("x", 0)), int(params.get("y", 0))),
        "type_text": lambda: type_text(params.get("text", "")),
        "key_press": lambda: key_press(params.get("keys", "")),
        "screenshot": lambda: screenshot(),
        "open_app": lambda: open_app(params.get("name", "")),
        "close_app": lambda: close_app(params.get("name", "")),
        "get_frontmost_app": lambda: get_frontmost_app(),
        "scroll": lambda: scroll(params.get("direction", "down"), int(params.get("amount", 5))),
        "drag": lambda: drag(int(params.get("x1", 0)), int(params.get("y1", 0)),
                             int(params.get("x2", 0)), int(params.get("y2", 0))),
        "applescript": lambda: raw_applescript(params.get("script", "")),
    }
    handler = dispatch.get(command)
    if not handler:
        return {"ok": False, "error": f"Unknown command: {command}",
                "available": list(dispatch.keys())}
    try:
        return handler()
    except Exception as e:
        return {"ok": False, "error": str(e)}