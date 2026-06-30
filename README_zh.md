# iCan-assistant

[English](./README.md) | 简体中文

## 这是什么

一个**可整目录复制**的 Claude Code 插件，把 Claude 变成 macOS 上的**办公副驾驶**。它内置两套后端和一个负责决策的路由/编排器：

- **本机 Apple Mail**（`scripts/mail.py`，基于 AppleScript）—— 读取/搜索/发送/回复、标记、移动、删除。
- **飞书 / Lark**（`lark` MCP 服务，通过 `.mcp.json` 捆绑）—— 文档/知识库、日历、任务、IM 消息。

它还能**编排多步工作流**——例如*读取多个文档 → 总结 → 发邮件 + 建飞书日历 + 建飞书任务*——按「收集 → 处理 → 执行」规划，并在各步骤间传递结果。

两种用法：作为**已安装插件**（技能、命令、MCP 服务自动加载），或作为**纯目录复制**（直接调用各部件）。见 [安装](#安装推荐通过插件市场) 与 [替代方案](#替代方案纯目录复制不走插件系统)。

## 目录结构

```
iCan-assistant/
├── .claude-plugin/plugin.json     # 插件清单
├── .mcp.json                      # 捆绑 lark MCP 服务（使用 ${CLAUDE_PLUGIN_ROOT}）
├── skills/
│   ├── office-router/SKILL.md     # 大脑：分类 → 路由 → 编排
│   └── local-email/SKILL.md       # 邮件使用说明（引擎 = scripts/mail.py）
├── scripts/
│   ├── mail.py                    # Apple Mail 引擎（封装 AppleScript 的 CLI）
│   └── lark-mcp.sh                # 自包含的 lark MCP 启动器
├── commands/
│   ├── office.md                  # /office —— 完整路由 + 编排
│   └── email.md                   # /email —— 仅邮件
├── .env.example
├── .gitignore
└── README.md
```

## 环境要求

- 装有 Mail.app 的 macOS（用于邮件）—— 终端需要对 “Mail” 的自动化（Automation）权限
  （系统设置 → 隐私与安全性 → 自动化）。无需完全磁盘访问权限。
- Node.js / `npx`（lark MCP 通过 `npx -y @larksuiteoapi/lark-mcp` 运行）。
- Python 3（用于 `mail.py`）。
- 一个飞书/Lark 自建应用（机器人）—— 见 [飞书 Bot 配置](#飞书-bot-配置开放平台)。

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

安装后，`office-router` / `local-email` 技能、`/office` 与 `/email` 命令，以及 `lark` MCP
服务会自动加载。`.mcp.json` 中的 `${CLAUDE_PLUGIN_ROOT}` 会解析到已安装的插件目录。

> **lark 重名问题：** 如果你要安装到的项目已在自己的 `.mcp.json` 中定义了 `lark` MCP
> 服务（本仓库即是如此），请先移除那一个，以免出现两个 `lark` 服务。全新项目只需插件自带的
> `lark`。

## 初始化（一次性）

三件插件无法替你捆绑的事：

1. **飞书凭据** —— 给 `lark` MCP server 提供 `FEISHU_APP_ID` / `FEISHU_APP_SECRET`
   （在 [飞书 Bot 配置](#飞书-bot-配置开放平台) 中创建）。不要把 `.env` 放进已安装的插件目录：
   它位于带版本号的 cache 路径下，插件升级后会丢失。二选一：
   - **推荐** —— 把 `.env` 放在固定位置，用 `FEISHU_ENV_FILE` 指过去：
     `export FEISHU_ENV_FILE=/abs/path/.env`（写进 shell profile）。`.env` 已被
     gitignore —— 切勿提交真实密钥。
   - **或** 直接导出环境变量：`export FEISHU_APP_ID=… FEISHU_APP_SECRET=…`。
2. **macOS 自动化权限** —— 首次使用邮件时，批准让终端控制 “Mail” 的弹窗
   （系统设置 → 隐私与安全性 → 自动化）。邮件功能仅限 macOS；飞书功能跨平台可用。
3. **飞书 Bot 权限与文档访问** —— 光有凭据还不够：bot 还需要正确的 API 权限，以及对你想让它
   读取的文档的明确访问权。见下一节。

## 飞书 Bot 配置（开放平台）

`lark` MCP 是以**你自己的飞书自建应用（机器人）** 身份访问飞书的。在开发者后台做一次性配置——
国内版飞书：<https://open.feishu.cn/app>（国际版 Lark：<https://open.larksuite.com/>）。下面的菜单名
按国内版飞书来写；Lark 上流程一致。

### 1. 创建应用，拿到凭据

开发者后台（<https://open.feishu.cn/app>）→ **创建企业自建应用**。进入**凭证与基础信息**，
复制 **App ID**（`cli_…`）和 **App Secret** —— 它们就是 `FEISHU_APP_ID` / `FEISHU_APP_SECRET`。

### 2. 开启机器人能力

添加应用能力 → 开启**机器人**。IM 消息以及下面的「群共享文档」都依赖它。

### 3. 开通 API 权限（scope）

权限管理 → 按插件用到的几个面开通权限（启动器启用的工具预设为 `im` / `calendar` / `doc` /
`task`）。需要 bot 执行写操作的，**读、写都要开**，例如：

| 面 | 代表性 scope |
|---|---|
| IM / 消息 | `im:message`、`im:message:send_as_bot`、`im:chat`、`im:resource` |
| 日历 | `calendar:calendar`（含日程创建/管理） |
| 云文档 / 知识库 / 云盘 | `docx:document`、`wiki:wiki`、`drive:drive`（只读用 `:readonly` 变体） |
| 任务 | `task:task` |

在权限管理里按关键词搜索 scope（消息 / 日历 / docx / wiki / drive / task），把每个面列出的相关
权限都开上。（如果需要 bot 按 id 解析用户，可另开 `contact:*:readonly` 类权限。）

### 4. 发布版本

版本管理与发布 → **创建版本** → 申请发布。企业自建应用需要**企业管理员审核通过**后，token 与
权限才会生效。

### 5. 让 Bot 能访问你的文档

已发布的应用能完成鉴权，但在你授权前它对**任何具体文档都没有访问权**。两种方式：

- **A. 用你自己的身份做 OAuth 授权**（个人副驾驶最省事）。启动器带 `--oauth --token-mode auto`：
  首个需要用户权限的调用会拉起浏览器授权；之后 MCP 以**你的**用户 token 身份访问，**你能看到的
  它就能读**，无需逐篇共享。若有提示，请把 lark-mcp 给出的回调地址加到应用的
  **安全设置 → 重定向 URL**。
- **B. 通过飞书群把文档共享给 bot**（bot 以自身身份访问——适合不想绑你个人 token 的团队文档）：
  1. 新建或打开一个飞书**群**。
  2. **把 bot 拉进群：** 群设置 → **群机器人** → **添加机器人** → 选择你的自建应用。
     （应用需已发布且开启了机器人能力。）
  3. **把文档共享给该群：** 打开文档 → **分享** → **添加协作者** → 搜索群名 → 设为
     **可阅读**（或可编辑）→ 完成。群里所有成员、**包括 bot**，都会继承这份访问权。
  4. **知识库（Wiki）** 的权限按空间/节点管理 —— 改为把 bot（或该群）加为知识库空间的成员。

> Bot 只能看到你共享给它的内容。若某次读取文档报权限错误，请回到第 5 步，针对那篇文档或那个知识库
> 空间再确认一次。

## 替代方案：纯目录复制（不走插件系统）

整个 `iCan-assistant/` 目录是自包含的——复制到任何位置都能直接用，无需安装：

- **邮件：** 直接运行 `python3 scripts/mail.py …`（无需 Claude）。
- **飞书 MCP：** 在宿主项目的 `.mcp.json` 中加入：
  `{"mcpServers":{"lark":{"command":"bash","args":["/abs/path/to/iCan-assistant/scripts/lark-mcp.sh"]}}}`
  并在脚本旁放一个 `.env`（启动器会自动发现）。
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
对外的操作。技能会指示 Claude 在执行前确认收件人/标题/正文/时间，并在意图不明时优先把邮件存为
**草稿**。如果你改编这些技能，请保留该行为。
