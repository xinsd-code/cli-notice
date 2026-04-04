---
name: setup-cli-notice
description: Use when enabling or troubleshooting the CLI Notice Codex plugin, including codex_hooks setup, environment variables, and local marketplace installation.
---

# CLI Notice Setup

Use this skill when the user wants to turn on or debug the CLI Notice plugin for
Codex.

## Setup checklist

1. Ensure the plugin exists at `integrations/cli-notice-codex` in the current repo,
   or copy it to `~/plugins/cli-notice-codex` for a home-local install.
2. Ensure a marketplace entry points to `./plugins/cli-notice-codex`.
3. Install hooks in an active Codex config layer:

For home-local use, copy `examples/codex-home-hooks-template.json` to
`~/.codex/hooks.json`.

4. Enable `codex_hooks` in `~/.codex/config.toml`:

```toml
[features]
codex_hooks = true
```

5. Optionally set environment variables before launching Codex:

```bash
export CLI_NOTICE_ENABLED="true"
export CLI_NOTICE_VOICE="Tingting"
export CLI_NOTICE_LANG="zh-CN"
export CLI_NOTICE_DEDUP_SECONDS="30"
```

## Expected behavior

- Best-effort approval reminder before risky Bash commands
- Completion reminder when Codex finishes a turn
- No interception of approval decisions

## Verification

- Start Codex in a workspace where the plugin is installed and an active
  `hooks.json` exists
- Trigger a risky command such as a write-heavy shell action
- Confirm that macOS `say` announces the reminder
