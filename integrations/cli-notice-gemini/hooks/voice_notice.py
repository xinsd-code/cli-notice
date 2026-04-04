#!/usr/bin/env python3
"""Native macOS voice reminders for Gemini hooks."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


DEFAULT_DEDUP_SECONDS = 30.0
TRUTHY_VALUES = {"1", "true", "yes", "on", "enabled"}
FALSY_VALUES = {"0", "false", "no", "off", "disabled"}


def load_payload() -> dict[str, Any]:
    try:
        raw = sys.stdin.read().strip()
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


def write_output(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))


def default_state_dir() -> Path:
    env_dir = os.getenv("CLI_NOTICE_STATE_DIR")
    if env_dir:
        return Path(env_dir).expanduser()

    tmpdir = os.getenv("TMPDIR") or tempfile.gettempdir()
    return Path(tmpdir) / "cli-notice"


def state_path() -> Path:
    state_dir = default_state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / "state.json"


def load_state() -> dict[str, float]:
    path = state_path()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict[str, float]) -> None:
    path = state_path()
    fd, tmp_path = tempfile.mkstemp(prefix="cli-notice-", suffix=".json", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def dedup_seconds() -> float:
    raw = os.getenv("CLI_NOTICE_DEDUP_SECONDS", str(DEFAULT_DEDUP_SECONDS))
    try:
        return max(1.0, float(raw))
    except ValueError:
        return DEFAULT_DEDUP_SECONDS


def recently_announced(key: str) -> bool:
    now = time.time()
    window = dedup_seconds()
    state = load_state()
    state = {entry: ts for entry, ts in state.items() if now - ts < max(window * 6, 600.0)}
    last_seen = state.get(key)
    if last_seen is not None and now - last_seen < window:
        return True
    state[key] = now
    save_state(state)
    return False


def language() -> str:
    return os.getenv("CLI_NOTICE_LANG", "zh-CN").lower()


def default_text(kind: str) -> str:
    if kind == "approval":
        override = os.getenv("CLI_NOTICE_APPROVAL_TEXT")
        if override:
            return override
        if language().startswith("zh"):
            return "Gemini 需要你确认，请看一下终端。"
        return "Gemini needs your confirmation. Please check the terminal."

    override = os.getenv("CLI_NOTICE_COMPLETE_TEXT")
    if override:
        return override
    if language().startswith("zh"):
        return "Gemini 已完成，请查看结果。"
    return "Gemini has finished. Please check the result."


def say(text: str) -> None:
    voice = os.getenv("CLI_NOTICE_VOICE", "Tingting")
    try:
        subprocess.Popen(
            ["say", "-v", voice, text],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        pass


def parse_bool(raw: str | None, *, default: bool) -> bool:
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in TRUTHY_VALUES:
        return True
    if normalized in FALSY_VALUES:
        return False
    return default


def cli_notice_enabled() -> bool:
    for name in ("CLI_NOTICE_ENABLED", "GEMINI_CLI_NOTICE_ENABLED", "CLI_NOTICE"):
        if name in os.environ:
            return parse_bool(os.environ.get(name), default=True)
    return True


def maybe_dump_payload(payload: dict[str, Any]) -> None:
    debug_dir = os.getenv("CLI_NOTICE_DEBUG_PAYLOAD_DIR")
    if not debug_dir:
        return
    try:
        target_dir = Path(debug_dir).expanduser()
        target_dir.mkdir(parents=True, exist_ok=True)
        stamp = int(time.time() * 1000)
        event = str(payload.get("hook_event_name") or "unknown").lower()
        (target_dir / f"{stamp}-{event}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except Exception:
        pass


def notification_key(payload: dict[str, Any]) -> str:
    details = payload.get("details")
    details_json = json.dumps(details, ensure_ascii=False, sort_keys=True) if isinstance(details, dict) else ""
    digest = hashlib.sha256(details_json.encode("utf-8")).hexdigest()[:12]
    return f"gemini:approval:{payload.get('notification_type')}:{digest}"


def completion_key(payload: dict[str, Any]) -> str:
    response = payload.get("prompt_response") or ""
    digest = hashlib.sha256(str(response).encode("utf-8")).hexdigest()[:12]
    session_id = payload.get("session_id") or "unknown-session"
    return f"gemini:complete:{session_id}:{digest}"


def is_confirmation_notification(payload: dict[str, Any]) -> bool:
    if payload.get("hook_event_name") != "Notification":
        return False
    if payload.get("notification_type") == "ToolPermission":
        return True

    haystack = " ".join(
        str(payload.get(field) or "")
        for field in ("notification_type", "message")
    ).lower()
    return any(word in haystack for word in ("approval", "confirm", "permission"))


def maybe_notify(payload: dict[str, Any]) -> None:
    if not cli_notice_enabled():
        return
    event = payload.get("hook_event_name")

    if event == "Notification" and is_confirmation_notification(payload):
        if not recently_announced(notification_key(payload)):
            say(default_text("approval"))
        return

    if event == "AfterAgent":
        if not payload.get("prompt_response"):
            return
        if payload.get("stop_hook_active"):
            return
        if not recently_announced(completion_key(payload)):
            say(default_text("complete"))


def main() -> int:
    payload = load_payload()
    maybe_dump_payload(payload)
    maybe_notify(payload)
    write_output({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
