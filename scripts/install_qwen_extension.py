#!/usr/bin/env python3
"""Install the CLI Notice Qwen extension into the local home environment.

Creates a timestamped backup plus a rollback script in the workspace before
modifying any home-directory files.
"""

from __future__ import annotations

import datetime as dt
import json
import shutil
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
EXTENSION_SRC = WORKSPACE / "integrations" / "cli-notice-qwen"
HOME = Path.home()
QWEN_SETTINGS = HOME / ".qwen" / "settings.json"
QWEN_EXTENSION_DIR = HOME / ".qwen" / "extensions" / "cli-notice-qwen"


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


def update_qwen_settings(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if data.get("disableAllHooks") is True:
        data["disableAllHooks"] = False
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_rollback_script(backup_dir: Path, metadata: dict[str, str]) -> Path:
    script = backup_dir / "rollback-qwen.sh"
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

    restore_file(str(QWEN_SETTINGS), metadata.get("qwen_settings_backup"))
    restore_dir(str(QWEN_EXTENSION_DIR), metadata.get("qwen_extension_backup"))

    lines.append('echo "Qwen rollback complete."')
    script.write_text("\n".join(lines) + "\n", encoding="utf-8")
    script.chmod(0o755)
    return script


def main() -> int:
    if not EXTENSION_SRC.exists():
        raise SystemExit(f"Missing extension source: {EXTENSION_SRC}")

    backup_dir = backup_root()
    metadata: dict[str, str] = {}

    backup = backup_file(QWEN_SETTINGS, backup_dir, "home/.qwen/settings.json")
    if backup:
        metadata["qwen_settings_backup"] = backup.relative_to(backup_dir).as_posix()
    backup = backup_dir_copy(QWEN_EXTENSION_DIR, backup_dir, "home/.qwen/extensions/cli-notice-qwen")
    if backup:
        metadata["qwen_extension_backup"] = backup.relative_to(backup_dir).as_posix()

    ensure_parent(QWEN_SETTINGS)
    QWEN_EXTENSION_DIR.parent.mkdir(parents=True, exist_ok=True)

    if QWEN_EXTENSION_DIR.exists() or QWEN_EXTENSION_DIR.is_symlink():
        if QWEN_EXTENSION_DIR.is_symlink() or QWEN_EXTENSION_DIR.is_file():
            QWEN_EXTENSION_DIR.unlink()
        else:
            shutil.rmtree(QWEN_EXTENSION_DIR)
    QWEN_EXTENSION_DIR.symlink_to(EXTENSION_SRC)

    update_qwen_settings(QWEN_SETTINGS)

    manifest = {
        "component": "qwen",
        "created_at": dt.datetime.now().isoformat(),
        "workspace": str(WORKSPACE),
        "extension_source": str(EXTENSION_SRC),
        "qwen_extension_dir": str(QWEN_EXTENSION_DIR),
        "qwen_settings": str(QWEN_SETTINGS),
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
