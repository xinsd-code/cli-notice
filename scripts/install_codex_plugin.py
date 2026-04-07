#!/usr/bin/env python3
"""Install the CLI Notice Codex plugin into the local home environment.

Creates a timestamped backup plus a rollback script in the workspace before
modifying any home-directory files.
"""

from __future__ import annotations

import datetime as dt
import json
import shutil
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
PLUGIN_SRC = WORKSPACE / "integrations" / "cli-notice-codex"
HOME = Path.home()
CODEX_CONFIG = HOME / ".codex" / "config.toml"
CODEX_HOOKS = HOME / ".codex" / "hooks.json"
HOME_PLUGIN_DIR = HOME / "plugins" / "cli-notice-codex"
HOME_MARKETPLACE = HOME / ".agents" / "plugins" / "marketplace.json"
HOME_PLUGIN_CACHE_DIR = HOME / ".codex" / "plugins" / "cache" / "local-home-marketplace" / "cli-notice-codex"


def backup_root() -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    root = WORKSPACE / "backups" / stamp
    root.mkdir(parents=True, exist_ok=False)
    return root


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def backup_file(src: Path, backup_dir: Path, rel_name: str) -> Path | None:
    if not src.exists():
        return None
    dst = backup_dir / rel_name
    ensure_parent(dst)
    shutil.copy2(src, dst)
    return dst


def backup_dir_copy(src: Path, backup_dir: Path, rel_name: str) -> Path | None:
    if not src.exists():
        return None
    dst = backup_dir / rel_name
    ensure_parent(dst)
    shutil.copytree(src, dst, dirs_exist_ok=True)
    return dst


def update_codex_config(path: Path) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if "[features]" in text:
        if "codex_hooks" in text:
            lines = []
            in_features = False
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("[") and stripped.endswith("]"):
                    in_features = stripped == "[features]"
                if in_features and stripped.startswith("codex_hooks"):
                    lines.append("codex_hooks = true")
                else:
                    lines.append(line)
            text = "\n".join(lines) + ("\n" if not text.endswith("\n") else "")
        else:
            lines = []
            inserted = False
            in_features = False
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("[") and stripped.endswith("]"):
                    if in_features and not inserted:
                        lines.append("codex_hooks = true")
                        inserted = True
                    in_features = stripped == "[features]"
                lines.append(line)
            if in_features and not inserted:
                lines.append("codex_hooks = true")
            text = "\n".join(lines) + ("\n" if not text.endswith("\n") else "")
    else:
        text = text.rstrip()
        if text:
            text += "\n\n"
        text += "[features]\ncodex_hooks = true\n"
    path.write_text(text, encoding="utf-8")


def write_codex_hooks(path: Path) -> None:
    script_path = HOME_PLUGIN_DIR / "scripts" / "voice_notice.py"
    hooks = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f'/usr/bin/python3 "{script_path}"',
                            "timeout": 5,
                        }
                    ],
                }
            ],
            "Stop": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": f'/usr/bin/python3 "{script_path}"',
                            "timeout": 5,
                        }
                    ],
                }
            ],
        }
    }
    path.write_text(json.dumps(hooks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_marketplace(path: Path) -> None:
    plugin_entry = {
        "name": "cli-notice-codex",
        "source": {
            "source": "local",
            "path": "./plugins/cli-notice-codex",
        },
        "policy": {
            "installation": "INSTALLED_BY_DEFAULT",
            "authentication": "ON_INSTALL",
        },
        "category": "Productivity",
    }
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {
            "name": "local-home-marketplace",
            "interface": {"displayName": "Local Home Marketplace"},
            "plugins": [],
        }

    plugins = data.setdefault("plugins", [])
    for idx, existing in enumerate(plugins):
        if existing.get("name") == "cli-notice-codex":
            plugins[idx] = plugin_entry
            break
    else:
        plugins.append(plugin_entry)

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_rollback_script(backup_dir: Path, metadata: dict[str, str]) -> Path:
    script = backup_dir / "rollback-codex.sh"
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
    ]

    def restore_file(target: str, backup_rel: str | None) -> None:
        if backup_rel:
            lines.extend(
                [
                    f"mkdir -p {json.dumps(str(Path(target).parent))}",
                    f"cp {json.dumps(str(backup_dir / backup_rel))} {json.dumps(target)}",
                    "",
                ]
            )
        else:
            lines.extend([f"rm -f {json.dumps(target)}", ""])

    def restore_dir(target: str, backup_rel: str | None) -> None:
        if backup_rel:
            lines.extend(
                [
                    f"rm -rf {json.dumps(target)}",
                    f"mkdir -p {json.dumps(str(Path(target).parent))}",
                    f"cp -R {json.dumps(str(backup_dir / backup_rel))} {json.dumps(target)}",
                    "",
                ]
            )
        else:
            lines.extend([f"rm -rf {json.dumps(target)}", ""])

    restore_file(str(CODEX_CONFIG), metadata.get("codex_config_backup"))
    restore_file(str(CODEX_HOOKS), metadata.get("codex_hooks_backup"))
    restore_file(str(HOME_MARKETPLACE), metadata.get("marketplace_backup"))
    restore_dir(str(HOME_PLUGIN_DIR), metadata.get("plugin_dir_backup"))
    restore_dir(str(HOME_PLUGIN_CACHE_DIR), metadata.get("plugin_cache_backup"))

    lines.append('echo "Codex rollback complete."')
    script.write_text("\n".join(lines) + "\n", encoding="utf-8")
    script.chmod(0o755)
    return script


def main() -> int:
    if not PLUGIN_SRC.exists():
        raise SystemExit(f"Missing plugin source: {PLUGIN_SRC}")

    backup_dir = backup_root()
    metadata: dict[str, str] = {}

    backup = backup_file(CODEX_CONFIG, backup_dir, "home/.codex/config.toml")
    if backup:
        metadata["codex_config_backup"] = backup.relative_to(backup_dir).as_posix()
    backup = backup_file(CODEX_HOOKS, backup_dir, "home/.codex/hooks.json")
    if backup:
        metadata["codex_hooks_backup"] = backup.relative_to(backup_dir).as_posix()
    backup = backup_file(HOME_MARKETPLACE, backup_dir, "home/.agents/plugins/marketplace.json")
    if backup:
        metadata["marketplace_backup"] = backup.relative_to(backup_dir).as_posix()
    backup = backup_dir_copy(HOME_PLUGIN_DIR, backup_dir, "home/plugins/cli-notice-codex")
    if backup:
        metadata["plugin_dir_backup"] = backup.relative_to(backup_dir).as_posix()
    backup = backup_dir_copy(
        HOME_PLUGIN_CACHE_DIR,
        backup_dir,
        "home/.codex/plugins/cache/local-home-marketplace/cli-notice-codex",
    )
    if backup:
        metadata["plugin_cache_backup"] = backup.relative_to(backup_dir).as_posix()

    ensure_parent(CODEX_CONFIG)
    ensure_parent(CODEX_HOOKS)
    ensure_parent(HOME_MARKETPLACE)
    HOME_PLUGIN_DIR.parent.mkdir(parents=True, exist_ok=True)

    shutil.rmtree(HOME_PLUGIN_DIR, ignore_errors=True)
    shutil.copytree(PLUGIN_SRC, HOME_PLUGIN_DIR)

    update_codex_config(CODEX_CONFIG)
    write_codex_hooks(CODEX_HOOKS)
    update_marketplace(HOME_MARKETPLACE)

    manifest = {
        "component": "codex",
        "created_at": dt.datetime.now().isoformat(),
        "workspace": str(WORKSPACE),
        "plugin_source": str(PLUGIN_SRC),
        "home_plugin_dir": str(HOME_PLUGIN_DIR),
        "home_plugin_cache_dir": str(HOME_PLUGIN_CACHE_DIR),
        "codex_config": str(CODEX_CONFIG),
        "codex_hooks": str(CODEX_HOOKS),
        "home_marketplace": str(HOME_MARKETPLACE),
        "backups": metadata,
    }
    (backup_dir / "install-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    rollback = write_rollback_script(backup_dir, metadata)
    print(json.dumps({"backup_dir": str(backup_dir), "rollback_script": str(rollback)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
