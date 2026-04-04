#!/usr/bin/env python3
"""Install the CLI Notice Gemini extension into the local home environment.

Creates a timestamped backup plus a rollback script in the workspace before
modifying any home-directory files.
"""

from __future__ import annotations

import datetime as dt
import json
import shutil
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
EXTENSION_SRC = WORKSPACE / "integrations" / "cli-notice-gemini"
HOME = Path.home()
GEMINI_SETTINGS = HOME / ".gemini" / "settings.json"
GEMINI_EXTENSION_DIR = HOME / ".gemini" / "extensions" / "cli-notice-gemini"


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


def update_gemini_settings(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    general = data.setdefault("general", {})
    general["enableNotifications"] = True
    hooks_config = data.setdefault("hooksConfig", {})
    hooks_config["enabled"] = True
    hooks_config["notifications"] = True
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_rollback_script(backup_dir: Path, metadata: dict[str, str]) -> Path:
    script = backup_dir / "rollback-gemini.sh"
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

    restore_file(str(GEMINI_SETTINGS), metadata.get("gemini_settings_backup"))
    restore_dir(str(GEMINI_EXTENSION_DIR), metadata.get("gemini_extension_backup"))

    lines.append('echo "Gemini rollback complete."')
    script.write_text("\n".join(lines) + "\n", encoding="utf-8")
    script.chmod(0o755)
    return script


def main() -> int:
    if not EXTENSION_SRC.exists():
        raise SystemExit(f"Missing extension source: {EXTENSION_SRC}")

    backup_dir = backup_root()
    metadata: dict[str, str] = {}

    backup = backup_file(GEMINI_SETTINGS, backup_dir, "home/.gemini/settings.json")
    if backup:
        metadata["gemini_settings_backup"] = backup.relative_to(backup_dir).as_posix()
    backup = backup_dir_copy(GEMINI_EXTENSION_DIR, backup_dir, "home/.gemini/extensions/cli-notice-gemini")
    if backup:
        metadata["gemini_extension_backup"] = backup.relative_to(backup_dir).as_posix()

    ensure_parent(GEMINI_SETTINGS)
    GEMINI_EXTENSION_DIR.parent.mkdir(parents=True, exist_ok=True)

    if GEMINI_EXTENSION_DIR.exists() or GEMINI_EXTENSION_DIR.is_symlink():
        if GEMINI_EXTENSION_DIR.is_symlink() or GEMINI_EXTENSION_DIR.is_file():
            GEMINI_EXTENSION_DIR.unlink()
        else:
            shutil.rmtree(GEMINI_EXTENSION_DIR)
    GEMINI_EXTENSION_DIR.symlink_to(EXTENSION_SRC)

    update_gemini_settings(GEMINI_SETTINGS)

    manifest = {
        "component": "gemini",
        "created_at": dt.datetime.now().isoformat(),
        "workspace": str(WORKSPACE),
        "extension_source": str(EXTENSION_SRC),
        "gemini_extension_dir": str(GEMINI_EXTENSION_DIR),
        "gemini_settings": str(GEMINI_SETTINGS),
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
