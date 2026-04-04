#!/usr/bin/env python3
"""Native macOS voice reminders for Codex hooks."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


DEFAULT_DEDUP_SECONDS = 30.0
TRUTHY_VALUES = {"1", "true", "yes", "on", "enabled"}
FALSY_VALUES = {"0", "false", "no", "off", "disabled"}
OPERATOR_TOKENS = {"&&", "||", ";", "|", "&"}
ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*$")

READ_ONLY_COMMANDS = (
    "cat",
    "cd",
    "echo",
    "env",
    "find",
    "git diff",
    "git log",
    "git show",
    "git status",
    "head",
    "ls",
    "pwd",
    "readlink",
    "rg",
    "sed -n",
    "tail",
    "which",
)

RISK_PATTERNS = {
    "destructive": re.compile(r"\b(rm|mv|chmod|chown|ln|truncate)\b"),
    "write": re.compile(r"\b(cp|mkdir|rmdir|touch|tee)\b|(^|[^>])>>?|sed\s+-i\b|perl\s+-pi\b"),
    "network": re.compile(r"\b(curl|wget|ssh|scp|rsync)\b"),
    "packages": re.compile(
        r"\b("
        r"brew\s+(install|upgrade)|"
        r"apt(-get)?\s+(install|upgrade|dist-upgrade)|"
        r"dnf\s+(install|upgrade)|"
        r"yum\s+(install|update)|"
        r"pip3?\s+install\b.*\s(--user|--break-system-packages)\b|"
        r"(npm|pnpm|yarn)\s+(install|add)\b.*\s-g\b|"
        r"cargo\s+install\b"
        r")"
    ),
}
REDIRECT_TARGET_RE = re.compile(r"(?:^|[;&|]\s*|\s)(?:>>|>)\s*([^\s;&|]+)")
WRITE_PATH_COMMANDS = {"chmod", "chown", "cp", "ln", "mkdir", "mv", "perl", "rm", "rmdir", "sed", "tee", "touch", "truncate"}
LAST_PATH_ONLY_COMMANDS = {"cp", "ln", "mv", "tee"}
SKIP_PATH_TOKENS = {"-", "--", "/dev/null"}


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
            return "Codex 可能需要你确认，请看一下终端。"
        return "Codex may need your confirmation. Please check the terminal."

    override = os.getenv("CLI_NOTICE_COMPLETE_TEXT")
    if override:
        return override
    if language().startswith("zh"):
        return "Codex 已完成，请查看结果。"
    return "Codex has finished. Please check the result."


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
    for name in ("CLI_NOTICE_ENABLED", "CODEX_CLI_NOTICE_ENABLED", "CLI_NOTICE"):
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


def normalized_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str):
        return ""
    return " ".join(command.strip().split())


def looks_read_only(command: str) -> bool:
    lower = command.lower()
    return any(lower.startswith(prefix) for prefix in READ_ONLY_COMMANDS)


def risk_bucket(command: str) -> str | None:
    lower = command.lower()
    if looks_read_only(lower):
        return None
    for bucket, pattern in RISK_PATTERNS.items():
        if pattern.search(lower):
            return bucket
    return None


def shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def primary_command(tokens: list[str]) -> tuple[str, int]:
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in OPERATOR_TOKENS:
            index += 1
            continue
        if ASSIGNMENT_RE.match(token):
            index += 1
            continue
        if token == "env":
            index += 1
            while index < len(tokens) and "=" in tokens[index] and not tokens[index].startswith(("/", "./", "../")):
                index += 1
            continue
        if token in {"command", "sudo", "nohup"}:
            index += 1
            continue
        return token, index
    return "", 0


def command_segments(tokens: list[str]) -> list[list[str]]:
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in OPERATOR_TOKENS:
            if current:
                segments.append(current)
                current = []
            continue
        current.append(token)
    if current:
        segments.append(current)
    return segments


def looks_like_path_token(token: str) -> bool:
    if not token or token in SKIP_PATH_TOKENS:
        return False
    if token.startswith("-"):
        return False
    if any(marker in token for marker in ("$(", "${", "*", "?", "[", "]")):
        return False
    return True


def normalize_candidate_path(token: str, cwd: str) -> Path | None:
    cleaned = token.strip("\"'")
    if not looks_like_path_token(cleaned):
        return None
    path = Path(cleaned).expanduser()
    if not path.is_absolute():
        path = Path(cwd) / path
    try:
        return path.resolve(strict=False)
    except Exception:
        return None


def candidate_paths(command: str, cwd: str) -> list[Path]:
    tokens = shell_tokens(command)
    if not tokens:
        return []

    candidates: list[Path] = []
    for raw in REDIRECT_TARGET_RE.findall(command):
        path = normalize_candidate_path(raw, cwd)
        if path is not None:
            candidates.append(path)

    for segment in command_segments(tokens):
        primary, start = primary_command(segment)
        if not primary or primary not in WRITE_PATH_COMMANDS:
            continue
        non_option_tokens = [token for token in segment[start + 1 :] if looks_like_path_token(token)]
        if primary in LAST_PATH_ONLY_COMMANDS and non_option_tokens:
            target = normalize_candidate_path(non_option_tokens[-1], cwd)
            if target is not None:
                candidates.append(target)
        else:
            for token in non_option_tokens:
                path = normalize_candidate_path(token, cwd)
                if path is not None:
                    candidates.append(path)

    return unique_paths(candidates)


def unique_paths(paths: list[Path]) -> list[Path]:
    unique_candidates: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        unique_candidates.append(path)
    return unique_candidates


def explicit_candidate_paths(command: str, cwd: str) -> list[Path]:
    candidates = []
    for path in candidate_paths(command, cwd):
        if "$" in str(path):
            continue
        candidates.append(path)
    return unique_paths(candidates)


def all_paths_within_cwd(paths: list[Path], cwd: str) -> bool:
    try:
        root = Path(cwd).resolve(strict=False)
    except Exception:
        return False

    if not paths:
        return False

    try:
        for path in paths:
            path.relative_to(root)
    except ValueError:
        return False
    return True


def likely_requires_manual_approval(payload: dict[str, Any], command: str, bucket: str) -> bool:
    permission_mode = str(payload.get("permission_mode") or "").lower()
    if permission_mode in {"plan", "dontask", "bypasspermissions", "never"}:
        return False

    approval_policy = str(payload.get("approval_policy") or payload.get("approvalPolicy") or "").lower()
    if approval_policy in {"never", "bypasspermissions"}:
        return False

    if bucket in {"network", "packages"}:
        return True

    cwd = str(payload.get("cwd") or "")
    if not cwd:
        return False

    paths = explicit_candidate_paths(command, cwd)
    if not paths:
        return False

    return not all_paths_within_cwd(paths, cwd)


def approval_key(command: str, bucket: str) -> str:
    digest = hashlib.sha256(command.encode("utf-8")).hexdigest()[:12]
    return f"codex:approval:{bucket}:{digest}"


def completion_key(payload: dict[str, Any]) -> str:
    turn_id = payload.get("turn_id") or "unknown-turn"
    return f"codex:complete:{turn_id}"


def maybe_notify_pre_tool(payload: dict[str, Any]) -> None:
    if not cli_notice_enabled():
        return
    if payload.get("hook_event_name") != "PreToolUse":
        return
    if payload.get("tool_name") != "Bash":
        return

    command = normalized_command(payload)
    if not command:
        return

    bucket = risk_bucket(command)
    if not bucket:
        return

    if not likely_requires_manual_approval(payload, command, bucket):
        return

    if recently_announced(approval_key(command, bucket)):
        return

    say(default_text("approval"))


def maybe_notify_stop(payload: dict[str, Any]) -> None:
    if not cli_notice_enabled():
        return
    if payload.get("hook_event_name") != "Stop":
        return
    if payload.get("stop_hook_active"):
        return
    if not payload.get("last_assistant_message"):
        return

    if recently_announced(completion_key(payload)):
        return

    say(default_text("complete"))


def output_for(payload: dict[str, Any]) -> dict[str, Any]:
    event = payload.get("hook_event_name")
    if event == "PreToolUse":
        return {
            "continue": True,
            "hookSpecificOutput": {"hookEventName": "PreToolUse"},
        }
    if event == "Stop":
        return {"continue": True}
    return {}


def main() -> int:
    payload = load_payload()
    maybe_dump_payload(payload)
    maybe_notify_pre_tool(payload)
    maybe_notify_stop(payload)
    write_output(output_for(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
