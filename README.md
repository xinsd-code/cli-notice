# CLI Notice

`CLI Notice` adds native macOS voice reminders to Codex CLI and Gemini CLI.
It helps you notice the moments that matter most while working in the terminal:

- when a CLI is likely waiting for your confirmation
- when a task has finished and the result is ready to review

The package is published as `@xinsd/cli-notice` and installs both integrations
through a single npm-driven workflow.

## Highlights

- Native voice reminders for Codex CLI
- Native voice reminders for Gemini CLI
- Install both integrations with one command
- Install only Codex or only Gemini if needed
- Backup and rollback built into the installer
- Runtime on/off switch with `CLI_NOTICE_ENABLED=true|false`
- macOS-first implementation using the system `say` command

## Install

Install the package:

```bash
npm i @xinsd/cli-notice
```

Install both integrations:

```bash
npx cli-notice all
```

Install only one integration:

```bash
npx cli-notice codex
```

```bash
npx cli-notice gemini
```

## What Gets Installed

Running the installer updates your real local CLI environment.

For Codex:

- copies the Codex integration to `~/plugins/cli-notice-codex`
- writes `~/.codex/hooks.json`
- enables `features.codex_hooks = true`
- updates `~/.agents/plugins/marketplace.json`

For Gemini:

- links the Gemini integration into `~/.gemini/extensions/cli-notice-gemini`
- enables notifications in `~/.gemini/settings.json`

Each installer creates a timestamped backup and rollback script before changing
your local environment.

## Quick Start

After installation, keep using your CLIs normally.

Examples:

```bash
codex
```

```bash
gemini
```

The reminders are automatic once the integration is installed.

## Runtime Toggle

You can turn reminders on or off per command:

```bash
CLI_NOTICE_ENABLED=true codex ...
CLI_NOTICE_ENABLED=false codex ...
```

```bash
CLI_NOTICE_ENABLED=true gemini ...
CLI_NOTICE_ENABLED=false gemini ...
```

## Configuration

Both integrations support the same environment variables:

```bash
export CLI_NOTICE_ENABLED="true"
export CLI_NOTICE_VOICE="Tingting"
export CLI_NOTICE_LANG="zh-CN"
export CLI_NOTICE_APPROVAL_TEXT="Please check the terminal."
export CLI_NOTICE_COMPLETE_TEXT="Task finished. Please review the result."
export CLI_NOTICE_DEDUP_SECONDS="30"
```

Defaults:

- `CLI_NOTICE_ENABLED=true`
- `CLI_NOTICE_VOICE=Tingting`
- `CLI_NOTICE_LANG=zh-CN`
- reminder dedup window: `30` seconds

## How It Works

### Codex

The Codex integration uses native hooks and a local voice script to announce:

- best-effort approval reminders before commands that are likely to require
  manual confirmation
- completion reminders when a turn finishes

Important limitation:

- Codex does not currently expose a dedicated native approval-request hook, so
  approval reminders are heuristic by design

### Gemini

The Gemini integration uses native extension hooks to announce:

- confirmation notifications when Gemini asks for tool permission
- completion reminders after the agent finishes a task

## Project Layout

The two integrations live side by side under `integrations/`:

- [integrations/cli-notice-codex](/Users/xinsd/Documents/vibe_coding/cli-notice/integrations/cli-notice-codex)
- [integrations/cli-notice-gemini](/Users/xinsd/Documents/vibe_coding/cli-notice/integrations/cli-notice-gemini)

Installers:

- [scripts/install_real_env.py](/Users/xinsd/Documents/vibe_coding/cli-notice/scripts/install_real_env.py)
- [scripts/install_codex_plugin.py](/Users/xinsd/Documents/vibe_coding/cli-notice/scripts/install_codex_plugin.py)
- [scripts/install_gemini_extension.py](/Users/xinsd/Documents/vibe_coding/cli-notice/scripts/install_gemini_extension.py)

CLI entry:

- [bin/cli-notice-install.js](/Users/xinsd/Documents/vibe_coding/cli-notice/bin/cli-notice-install.js)

## Component Docs

Integration-specific documentation:

- Codex:
  [integrations/cli-notice-codex/README.md](/Users/xinsd/Documents/vibe_coding/cli-notice/integrations/cli-notice-codex/README.md)
- Gemini:
  [integrations/cli-notice-gemini/README.md](/Users/xinsd/Documents/vibe_coding/cli-notice/integrations/cli-notice-gemini/README.md)

Release history:

- [CHANGELOG.md](/Users/xinsd/Documents/vibe_coding/cli-notice/CHANGELOG.md)

## Local Development

If you are working directly in this repository, you can still run the Python
installers without going through npm:

```bash
python3 scripts/install_real_env.py
```

```bash
python3 scripts/install_codex_plugin.py
```

```bash
python3 scripts/install_gemini_extension.py
```

You can also verify the npm package shape locally with:

```bash
npm pack --dry-run
```

## Notes

- macOS is the primary supported platform in the current release
- speech playback failures are fail-open and do not block the CLI session
- Codex approval reminders are intentionally conservative to reduce false
  positives during normal workspace-local file operations

## License

MIT. See [LICENSE](/Users/xinsd/Documents/vibe_coding/cli-notice/LICENSE).
