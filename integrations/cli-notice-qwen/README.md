# CLI Notice Qwen

`cli-notice-qwen` 是一个面向 macOS 的 Qwen Code 原生语音提醒扩展，用来在
Qwen CLI 工作过程中提醒使用者关注终端里的关键时刻。

## 功能介绍

- 当 Qwen 即将弹出权限确认对话框时，语音提醒你查看终端
- 当 Qwen 当前一轮响应完成时，语音提醒你回来查看结果
- 不改变原本的 `qwen` 命令使用方式
- 不接管审批，不替代 Qwen 原生确认界面
- 使用 Qwen 原生 extension / hooks 机制，不依赖后台守护进程

## 工作方式

当前扩展包含：

- 扩展清单 `qwen-extension.json`
- hooks 配置 `hooks/hooks.json`
- 语音脚本 `hooks/voice_notice.py`

使用的 Qwen hooks 事件：

- `PermissionRequest`
  作用：在权限对话框真正弹出前做确认提醒
- `Stop`
  作用：在当前响应结束前做完成提醒
- `Notification`
  作用：对 `permission_prompt` 做兼容兜底

这里优先使用 `PermissionRequest`，因为它比泛化的通知事件更准确，能更稳定地对应“马上要弹审批框”的时机。

## 依赖要求

- macOS
- 已安装 `qwen`
- 系统可用 `say`
- 建议 `python3` 可直接运行

## 快速部署

推荐的 npm 安装方式是：

```bash
npm i @xinsd/cli-notice
npx cli-notice qwen
```

这会安装 Qwen 语音提醒扩展，并自动备份相关本地配置。

如果你就在这个仓库里开发，也可以直接在仓库根目录执行：

```bash
python3 scripts/install_qwen_extension.py
```

## 手动部署

### 1. 链接扩展

在仓库根目录执行：

```bash
qwen extensions link "$(pwd)/integrations/cli-notice-qwen"
```

### 2. 确认 hooks 没被全局禁用

在 `~/.qwen/settings.json` 中确认没有：

```json
{
  "disableAllHooks": true
}
```

如果存在，把它删掉或改成 `false`。

## 使用方法

配置完成后，正常使用 `qwen` 即可。

常见触发场景：

- 当 Qwen 请求工具权限确认时
  作用：播放“Qwen 需要你确认，请看一下终端。”
- 当 Qwen 当前响应完成时
  作用：播放“Qwen 已完成，请查看结果。”

## 可选环境变量

```bash
export CLI_NOTICE_VOICE="Tingting"
export CLI_NOTICE_LANG="zh-CN"
export CLI_NOTICE_APPROVAL_TEXT="Qwen 需要你确认，请看一下终端。"
export CLI_NOTICE_COMPLETE_TEXT="Qwen 已完成，请查看结果。"
export CLI_NOTICE_DEDUP_SECONDS="30"
export CLI_NOTICE_ENABLED="true"
```

## 启动时控制开关

最直接的方式是启动时传环境变量：

```bash
CLI_NOTICE_ENABLED=true qwen ...
CLI_NOTICE_ENABLED=false qwen ...
```

## 验证方法

### 验证完成提醒

执行一条正常会结束的 Qwen 任务，当前响应结束后应听到完成播报。

### 验证确认提醒

执行一条会触发工具权限审批的 Qwen 任务，在确认对话框出现前应先听到确认提醒。

## 已知说明

- 这个扩展不会拦截或自动批准任何操作
- 如果语音播放失败，Qwen 任务会继续，不会被中断
- 当前实现依赖 Qwen 0.14.0 已提供的原生 hooks 事件

## 回退

如果你通过安装脚本部署，直接执行对应备份目录里的：

```bash
./backups/<timestamp>/rollback-qwen.sh
```

如果你是手动部署，可以手动移除：

- `~/.qwen/extensions/cli-notice-qwen`
- `~/.qwen/settings.json` 中你为 hooks 做的相关修改

## 相关文件

- 扩展清单：
  [qwen-extension.json](/Users/xinsd/Documents/vibe_coding/cli-notice/integrations/cli-notice-qwen/qwen-extension.json)
- hooks 配置：
  [hooks.json](/Users/xinsd/Documents/vibe_coding/cli-notice/integrations/cli-notice-qwen/hooks/hooks.json)
- 语音脚本：
  [voice_notice.py](/Users/xinsd/Documents/vibe_coding/cli-notice/integrations/cli-notice-qwen/hooks/voice_notice.py)
