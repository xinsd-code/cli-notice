# CLI Notice Codex

`cli-notice-codex` 是一个面向 macOS 的 Codex 原生语音提醒插件，用来在
Codex CLI 工作过程中提醒使用者关注终端里的关键时刻。

## 功能介绍

- 在 Codex 即将执行高风险 Bash 操作时，做一次“可能需要你确认”的语音提醒
- 这类提醒会尽量只在“高概率真的会弹人工确认”的情况下触发，避免普通工作区写操作误报
- 在 Codex 一轮任务结束时，播报“任务已完成”的语音提醒
- 不改变你原本的 `codex` 使用方式
- 不接管审批，不替代 Codex 原生确认界面
- 通过官方 Codex hooks 配置层工作，兼容 repo-local 和 home-local 两种部署方式

## 工作方式

这个插件本身提供：

- 官方格式的 Codex 插件 manifest
- 一个 setup skill
- 一个本地语音 hook 脚本 `scripts/voice_notice.py`

真正触发提醒的 hooks 不写在 `plugin.json` 里，而是写在：

- `~/.codex/hooks.json`

当前插件使用两个事件：

- `PreToolUse`
  作用：在识别到高风险 Bash 命令时做最佳努力提醒
- `Stop`
  作用：在当前任务结束时播报完成提醒

## 依赖要求

- macOS
- 已安装 `codex`
- 系统可用 `say`
- 建议 `python3` 可直接运行

## 快速部署

推荐的 npm 安装方式是：

```bash
npm i @xinsd/cli-notice
npx cli-notice codex
```

这会自动完成下面几件事：

- 备份你当前的 Codex / Gemini 本地配置
- 复制插件到 `~/plugins/cli-notice-codex`
- 写入 `~/.codex/hooks.json`
- 打开 `~/.codex/config.toml` 里的 `features.codex_hooks = true`
- 更新 `~/.agents/plugins/marketplace.json`

安装脚本会在仓库 `backups/` 下生成带时间戳的回退目录和回退脚本。

如果你就在这个仓库里开发，也可以直接在仓库根目录执行：

```bash
python3 scripts/install_codex_plugin.py
```

## 手动部署

### 1. 复制插件到 home 目录

在仓库根目录执行：

```bash
mkdir -p ~/plugins
rsync -a integrations/cli-notice-codex/ ~/plugins/cli-notice-codex/
```

### 2. 配置插件 marketplace

把 [examples/codex-home-marketplace-entry.json](/Users/xinsd/Documents/vibe_coding/cli-notice/examples/codex-home-marketplace-entry.json)
里的插件条目合并到：

- `~/.agents/plugins/marketplace.json`

### 3. 安装 hooks

把
[examples/codex-home-hooks-template.json](/Users/xinsd/Documents/vibe_coding/cli-notice/examples/codex-home-hooks-template.json)
复制成 `~/.codex/hooks.json`

### 4. 打开 Codex hooks 功能

在 `~/.codex/config.toml` 中加入：

```toml
[features]
codex_hooks = true
```

也可以参考：

- [codex-config-snippet.toml](/Users/xinsd/Documents/vibe_coding/cli-notice/examples/codex-config-snippet.toml)

## 使用方法

配置完成后，正常使用 `codex` 即可，不需要额外包一层命令。

常见触发场景：

- 当 Codex 准备执行写文件、删除、网络、安装依赖等高风险 Bash 操作时
  作用：播放“Codex 可能需要你确认，请看一下终端。”
- 当 Codex 当前任务结束时
  作用：播放“Codex 已完成，请查看结果。”

## 可选环境变量

```bash
export CLI_NOTICE_VOICE="Tingting"
export CLI_NOTICE_LANG="zh-CN"
export CLI_NOTICE_APPROVAL_TEXT="Codex 可能需要你确认，请看一下终端。"
export CLI_NOTICE_COMPLETE_TEXT="Codex 已完成，请查看结果。"
export CLI_NOTICE_DEDUP_SECONDS="30"
export CLI_NOTICE_ENABLED="true"
```

## 启动时控制开关

最直接的方式是启动时传环境变量：

```bash
CLI_NOTICE_ENABLED=true codex ...
CLI_NOTICE_ENABLED=false codex ...
```

## 验证方法

### 验证完成提醒

进入带有 hooks 的工作目录，正常发起一轮 Codex 任务。任务结束后应听到完成播报。

### 验证确认提醒

让 Codex 执行一个明显会触发审批的写操作，例如创建 `/tmp` 下文件。出现审批前，应先听到确认提醒。

## 已知说明

- Codex 当前没有独立的“审批请求”原生 hook，所以确认提醒仍然是基于 `PreToolUse` 做的最佳努力判断
- 当前实现已经收紧为“更像真的会触发人工确认”才播报，尽量避免普通工作区写操作误报
- 这个插件不会拦截或自动批准任何操作
- 如果语音播放失败，Codex 任务会继续，不会被中断

## 回退

如果你是通过安装脚本部署的，直接执行对应备份目录下的：

```bash
./backups/<timestamp>/rollback.sh
```

## 相关文件

- 插件 manifest：
  [plugin.json](/Users/xinsd/Documents/vibe_coding/cli-notice/integrations/cli-notice-codex/.codex-plugin/plugin.json)
- 语音脚本：
  [voice_notice.py](/Users/xinsd/Documents/vibe_coding/cli-notice/integrations/cli-notice-codex/scripts/voice_notice.py)
- setup skill：
  [SKILL.md](/Users/xinsd/Documents/vibe_coding/cli-notice/integrations/cli-notice-codex/skills/setup-cli-notice/SKILL.md)
