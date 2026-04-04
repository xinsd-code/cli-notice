# Changelog

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
