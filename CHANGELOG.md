# Changelog

## 0.1.3 - 2026-04-07

- Fixed `cli-notice-qwen` hook command expansion so the Qwen extension now runs
  from the installed extension directory correctly
- Fixed `cli-notice-qwen` completion reminders for real `Stop` payloads where
  `stop_hook_active` is `true`
- Improved Codex approval reminder detection for variable-based outside-workspace
  writes such as `target=/tmp/... && touch "$target"`
- Kept Codex approval reminders conservative so normal workspace-local commands
  and the SQL backup flow do not regress into false positives
- Revalidated the updated Codex and Qwen integrations against the real local CLI
  environments

## 0.1.2 - 2026-04-07

- Added `cli-notice-qwen`, a native Qwen Code extension with:
  - approval reminders via `PermissionRequest`
  - completion reminders via `Stop`
- Added `scripts/install_qwen_extension.py`
- Updated `npx cli-notice all` to install Codex, Gemini, and Qwen together
- Removed Codex hook `statusMessage` noise from the installed hook config and template
- Updated npm package metadata and root docs for the new Qwen integration

## 0.1.1 - 2026-04-04

- Refreshed the root `README.md` to read more like a polished open source
  project homepage
- Synced npm package metadata for the updated documentation release
- Revalidated Gemini approval reminders against a real `ToolPermission`
  notification flow

## 0.1.0 - 2026-04-04

- Initial public release of `@xinsd/cli-notice`
- Added npm install flow:
  - `npm i @xinsd/cli-notice`
  - `npx cli-notice all|codex|gemini`
- Added standalone installers for:
  - Codex plugin
  - Gemini extension
- Added macOS voice reminders for:
  - Codex approval moments
  - Codex task completion
  - Gemini confirmation notifications
  - Gemini task completion
- Added runtime toggle support with `CLI_NOTICE_ENABLED=true|false`
- Reduced false-positive Codex approval reminders for normal workspace-local file operations
- Consolidated both integrations under `integrations/` for simpler publishing and maintenance
