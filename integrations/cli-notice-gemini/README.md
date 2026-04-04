# CLI Notice Gemini

`cli-notice-gemini` 是一个面向 macOS 的 Gemini CLI 语音提醒扩展，用来在
Gemini CLI 需要人工确认或者任务完成时，通过系统语音提醒终端使用者。

## 功能介绍

- 当 Gemini 发出工具权限确认通知时，语音提醒你查看终端
- 当 Gemini 当前任务完成时，语音提醒你回来查看结果
- 不改变原本的 `gemini` 命令使用方式
- 不接管 Gemini 的审批逻辑，只做提醒
- 使用 Gemini 原生 hooks / extensions 机制，不依赖后台守护进程

## 工作方式

当前扩展包含：

- 扩展清单 `gemini-extension.json`
- hooks 配置 `hooks/hooks.json`
- 语音脚本 `hooks/voice_notice.py`

使用的 Gemini hooks 事件：

- `Notification`
  作用：捕获 `ToolPermission` 这类确认通知
- `AfterAgent`
  作用：在任务完成后做完成提醒

这里没有使用 `SessionEnd`，因为它只会在整个 Gemini CLI 进程退出时触发，
不适合“每次任务完成都提醒”的目标。

## 依赖要求

- macOS
- 已安装 `gemini`
- 系统可用 `say`
- 建议 `python3` 可直接运行

## 快速部署

推荐的 npm 安装方式是：

```bash
npm i @xinsd/cli-notice
npx cli-notice gemini
```

这会安装 Gemini 语音提醒扩展，并自动备份相关本地配置。

如果你就在这个仓库里开发，也可以直接在仓库根目录执行：

```bash
python3 scripts/install_gemini_extension.py
```

## 手动部署

### 1. 链接扩展

在仓库根目录执行：

```bash
gemini extensions link "$(pwd)/integrations/cli-notice-gemini"
```

### 2. 打开 Gemini 通知与 hooks

在 `~/.gemini/settings.json` 中确认以下配置为开启状态：

```json
{
  "general": {
    "enableNotifications": true
  },
  "hooksConfig": {
    "enabled": true,
    "notifications": true
  }
}
```

也可以参考：

- [gemini-settings-snippet.json](/Users/xinsd/Documents/vibe_coding/cli-notice/examples/gemini-settings-snippet.json)

## 使用方法

配置完成后，正常使用 `gemini` 即可。

常见触发场景：

- 当 Gemini 请求工具权限确认时
  作用：播放“Gemini 需要你确认，请看一下终端。”
- 当 Gemini 当前任务完成时
  作用：播放“Gemini 已完成，请查看结果。”

## 可选环境变量

```bash
export CLI_NOTICE_VOICE="Tingting"
export CLI_NOTICE_LANG="zh-CN"
export CLI_NOTICE_APPROVAL_TEXT="Gemini 需要你确认，请看一下终端。"
export CLI_NOTICE_COMPLETE_TEXT="Gemini 已完成，请查看结果。"
export CLI_NOTICE_DEDUP_SECONDS="30"
export CLI_NOTICE_ENABLED="true"
```

## 启动时控制开关

最直接的方式是启动时传环境变量：

```bash
CLI_NOTICE_ENABLED=true gemini ...
CLI_NOTICE_ENABLED=false gemini ...
```

## 验证方法

### 验证完成提醒

执行一条正常会结束的 Gemini 任务，完成后应听到完成播报。

### 验证确认提醒

执行一条会触发工具权限审批的 Gemini 任务，在确认弹出前应听到确认提醒。

## 已知说明

- 扩展只负责提醒，不会代替 Gemini 做批准或拒绝
- 如果语音播放失败，Gemini 会继续执行，不会因为提醒失败而中断

## 回退

如果你通过安装脚本部署，直接执行对应备份目录里的：

```bash
./backups/<timestamp>/rollback.sh
```

如果你是手动部署，可以手动移除：

- `~/.gemini/extensions/cli-notice-gemini`
- `~/.gemini/settings.json` 中相关开启项

## 相关文件

- 扩展清单：
  [gemini-extension.json](/Users/xinsd/Documents/vibe_coding/cli-notice/integrations/cli-notice-gemini/gemini-extension.json)
- hooks 配置：
  [hooks.json](/Users/xinsd/Documents/vibe_coding/cli-notice/integrations/cli-notice-gemini/hooks/hooks.json)
- 语音脚本：
  [voice_notice.py](/Users/xinsd/Documents/vibe_coding/cli-notice/integrations/cli-notice-gemini/hooks/voice_notice.py)
