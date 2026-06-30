# iCan-assistant

[English](./README.md) | 简体中文

## 项目简介

一个**可整目录复制**的 Claude Code 插件，把 Claude 变成 macOS 上的**办公副驾驶**。它内置两套后端和一个负责决策的路由/编排器：

- **本机 Apple Mail**（`scripts/mail.py`，基于 AppleScript）—— 读取/搜索/发送/回复、标记、移动、删除。
- **飞书 / Lark**（通过 **`lark-cli`** 与 `lark-*` 技能）—— 文档/知识库、日历、任务、IM、多维表格、电子表格、妙记、视频会议、审批、OKR、云盘等。飞书操作以**你本人身份**执行（不是机器人身份）。

它还能**编排多步工作流**——例如*读取多个文档 → 总结 → 发邮件 + 建飞书日历 + 建飞书任务*——按「收集 → 处理 → 执行」规划，并在各步骤间传递结果。

两种用法：作为**已安装插件**（技能、命令自动加载），或作为**纯目录复制**（直接调用各部件）。见 [安装](#安装推荐通过插件市场) 与 [替代方案](#替代方案纯目录复制不走插件系统)。

## 目录结构

```
iCan-assistant/
├── .claude-plugin/plugin.json     # 插件清单
├── skills/
│   ├── office-router/SKILL.md     # 大脑：分类 → 路由 → 编排
│   └── local-email/SKILL.md       # 邮件使用说明（引擎 = scripts/mail.py）
├── scripts/
│   └── mail.py                    # Apple Mail 引擎（封装 AppleScript 的 CLI）
├── commands/
│   ├── office.md                  # /office —— 完整路由 + 编排
│   └── email.md                   # /email —— 仅邮件
├── .gitignore
└── README.md
```

## 环境要求

- 装有 Mail.app 的 macOS（用于邮件）—— 终端需要对 “Mail” 的自动化（Automation）权限
  （系统设置 → 隐私与安全性 → 自动化）。无需完全磁盘访问权限。
- Python 3（用于 `mail.py`）。
- **`lark-cli`**（飞书侧）—— 安装并登录一次（见 [飞书配置](#飞书配置lark-cli)）。它内置的
  `lark-*` 技能驱动文档/日历/任务/IM/多维表格等全部飞书操作。

## 安装（推荐：通过插件市场）

本仓库自身就是一个 Claude Code 插件**市场**（清单位于
`.claude-plugin/marketplace.json`，市场名为 `ican`；插件位于仓库根目录）。该仓库是
**公开（public）** 的——无需 GitHub 登录或 SSH 密钥。安装方法：

```
# 1. 添加市场
/plugin marketplace add https://github.com/chuanwen-wu/iCan-assistant.git
#   或者，从本地克隆添加：
/plugin marketplace add /path/to/iCan-assistant

# 2. 安装插件
/plugin install ican-assistant@ican

# 3.（可选：交互式浏览）
/plugin
```

安装后，`office-router` / `local-email` 技能与 `/office`、`/email` 命令会自动加载。飞书后端
使用宿主机上的 `lark-cli`（插件不再捆绑 MCP 服务）。

## 初始化（一次性）

三件插件无法替你捆绑的事：

1. **`lark-cli` + 飞书登录** —— 见 [飞书配置](#飞书配置lark-cli)。安装 `lark-cli`，以本人身份
   登录并固定为用户身份。
2. **macOS 自动化权限** —— 首次使用邮件时，批准让终端控制 “Mail” 的弹窗
   （系统设置 → 隐私与安全性 → 自动化）。邮件功能仅限 macOS；飞书功能跨平台可用。
3. **飞书应用权限** —— 光登录还不够：应用还需要为你用到的几个面开通正确的 API 权限。见下一节。

## 飞书配置（lark-cli）

飞书后端通过 **`lark-cli`** 访问飞书，以**你本人的用户身份**、在你自己的自建应用下运行。应用
配置与现有设置保持不变（仍是同一个 App ID `cli_a97286141d785bc4`）；你只需以本人身份登录。

### 1. 安装 lark-cli

```
brew install lark-cli          # 或按 lark-cli 安装文档选择适合你系统的方式
lark-cli --version
```

### 2. 以本人身份登录并固定用户身份

```
lark-cli auth login            # 在该应用下以你本人身份做设备码登录
lark-cli config default-as user
lark-cli whoami                # 确认："identity": "user"，"tokenStatus": "ready"
```

`auth login` 会拉起设备码授权；完成后 `lark-cli` 持有**你的**用户 token 并以你的身份行事——
**你能看到的它就能读/操作**，无需逐篇共享文档。`config default-as user` 让用户身份成为每次调用
的默认身份。

### 3. 开通 API 权限（scope）

在开发者后台（国内版飞书：<https://open.feishu.cn/app>，国际版 Lark：
<https://open.larksuite.com/>）→ **权限管理** → 按你用到的面开通权限。需要执行写操作的，
**读、写都要开**，例如：

| 面 | 代表性 scope |
|---|---|
| IM / 消息 | `im:message`、`im:chat`、`im:resource` |
| 日历 | `calendar:calendar`（含日程创建/管理） |
| 云文档 / 知识库 / 云盘 | `docx:document`、`wiki:wiki`、`drive:drive`（只读用 `:readonly` 变体） |
| 任务 | `task:task` |
| 多维表格 / 电子表格 | `bitable:app`、`sheets:spreadsheet` |
| 妙记 / 视频会议 | `minutes:minutes`、`vc:*`（读） |
| 通讯录（按 id 解析用户） | `contact:*:readonly` |

在权限管理里按关键词搜索 scope，把每个面列出的相关权限都开上。若某次调用报权限错误，补上缺失的
scope，必要时重新发布版本，再重试。由于你以本人身份行事，文档访问跟随**你自己**的权限——无需把
文档共享给机器人。

## 替代方案：纯目录复制（不走插件系统）

整个 `iCan-assistant/` 目录是自包含的——复制到任何位置都能直接用，无需安装：

- **邮件：** 直接运行 `python3 scripts/mail.py …`（无需 Claude）。
- **飞书：** 确保已安装并登录 `lark-cli`（见上面步骤），用 `lark-cli <domain> …` 驱动
  （例如 `lark-cli calendar +agenda`）。
- **路由/编排逻辑：** 不安装时技能不会自动触发——把
  `skills/office-router/SKILL.md` 里的关键规则复制进项目的 `CLAUDE.md`/`AGENTS.md`，或手动调用技能。

## 使用

- `/office <请求>` —— 跨邮件 + 飞书的路由 + 多步编排。
- `/email <请求>` —— 仅邮件。
- 或直接自然语言提问（“看下我未读邮件”、“总结这几个飞书文档并发给老板”）——
  `office-router` 技能会在邮件/飞书/办公工作流类请求上自动触发。

独立使用（无需 Claude），邮件引擎可单独工作：

```bash
python3 scripts/mail.py --help
python3 scripts/mail.py list --limit 10 --unread
```

## 安全

发送/回复邮件、发 IM 消息、创建/修改日历事件或任务、删除/移动邮件、共享文档，都是真实的、
对外的操作。技能会指示 Claude 在执行前确认收件人/标题/正文/时间、遵守 `lark-cli` 的风险分级
（绝不自动确认 `high-risk-write`），并在意图不明时优先把邮件存为**草稿**。如果你改编这些技能，
请保留该行为。
