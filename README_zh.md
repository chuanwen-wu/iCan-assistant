# iCan-assistant

[English](./README.md) | 简体中文

## 项目简介

一个**可整目录复制**的 Claude Code 插件，把 Claude 变成 macOS 上的**办公助手**。它内置两套后端和一个负责决策的路由/编排器：

- **本机 Apple Mail**（`scripts/mail.py`，基于 AppleScript）—— 读取/搜索/发送/回复、标记、移动、删除。
- **飞书 / Lark**（`lark` MCP 服务，通过 `.mcp.json` 捆绑）—— 文档/知识库、日历、任务、IM 消息。
  访问是**以用户授权**进行的：服务通过 OAuth 用**你本人的**用户 token 行事，因此它能看到、能做的，
  始终不超出你本人的权限范围。**首次**调用飞书会拉起浏览器让你授权（见
  [飞书应用配置](#飞书应用配置开放平台)）。

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
- 一个飞书/Lark 自建应用 —— 见 [飞书应用配置](#飞书应用配置开放平台)。

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
   （在 [飞书应用配置](#飞书应用配置开放平台) 中创建）。不要把 `.env` 放进已安装的插件目录：
   它位于带版本号的 cache 路径下，插件升级后会丢失。二选一：
   - **推荐** —— 把 `.env` 放在固定位置，用 `FEISHU_ENV_FILE` 指过去：
     `export FEISHU_ENV_FILE=/abs/path/.env`（写进 shell profile）。`.env` 已被
     gitignore —— 切勿提交真实密钥。
   - **或** 直接导出环境变量：`export FEISHU_APP_ID=… FEISHU_APP_SECRET=…`。
2. **macOS 自动化权限** —— 首次使用邮件时，批准让终端控制 “Mail” 的弹窗
   （系统设置 → 隐私与安全性 → 自动化）。邮件功能仅限 macOS；飞书功能跨平台可用。
3. **飞书应用权限与用户授权** —— 光有凭据还不够。应用既需要正确的 API 权限，**也需要你本人授权**：
   它不会用应用级 token 读你的数据，而是通过 OAuth 用**你的**用户 token 行事。这意味着要做两件事：
   （a）在开发者后台的重定向 URL 列表里登记 OAuth 回调地址 `http://localhost:3000/callback`；
   （b）首次使用时在浏览器里完成一次性授权。见下一节。

## 飞书应用配置（开放平台）

`lark` MCP 是以**你自己的飞书自建应用**身份访问飞书的。它**不**用应用级 token 读你的数据，而是
通过 OAuth 用**你的**用户 token 行事：你在浏览器里授权一次，MCP 缓存换来的用户 token，之后它能做的
就跟你本人的飞书账号一模一样。在开发者后台做一次性配置——国内版飞书：<https://open.feishu.cn/app>
（国际版 Lark：<https://open.larksuite.com/>）。下面的菜单名按国内版飞书来写；Lark 上流程一致。

### 1. 创建应用，拿到凭据

开发者后台（<https://open.feishu.cn/app>）→ **创建企业自建应用**。进入**凭证与基础信息**，
复制 **App ID**（`cli_…`）和 **App Secret** —— 它们就是 `FEISHU_APP_ID` / `FEISHU_APP_SECRET`。

### 2. 开通 API 权限（scope）

权限管理 → 按插件用到的几类能力开通权限（启动器启用的工具预设为 `im` / `calendar` / `doc` /
`task`）。需要执行写操作的，**读、写都要开**，例如：

| 能力 | 代表性 scope |
|---|---|
| IM / 消息 | `im:message`、`im:chat`、`im:resource` |
| 日历 | `calendar:calendar`（含日程创建/管理） |
| 云文档 / 知识库 / 云盘 | `docx:document`、`wiki:wiki`、`drive:drive`（只读用 `:readonly` 变体） |
| 任务 | `task:task` |

在权限管理里按关键词搜索 scope（消息 / 日历 / docx / wiki / drive / task），把每类列出的相关
权限都开上。（如果需要按 id 解析用户，可另开 `contact:*:readonly` 类权限。）

### 3. 发布版本

版本管理与发布 → **创建版本** → 申请发布。企业自建应用需要**企业管理员审核通过**后，token 与
权限才会生效。

### 4. 登记 OAuth 回调地址

OAuth 需要一个回调地址，把授权码交还回本地。启动器以 `--oauth` 方式运行 lark-mcp，它的回调地址
固定在本机的 **`http://localhost:3000/callback`**，所以后台登记的必须正是这个地址——否则飞书会以
*redirect_uri 不匹配* 拒绝授权。在开发者后台打开 **安全设置 → 重定向 URL**，添加：

```
http://localhost:3000/callback
```

（若你改了端口，请登记对应的地址。回调只在你本机提供服务，不会对外暴露。）

### 5. 以你本人身份授权（首次浏览器登录）

启动器带 `--oauth --token-mode auto`，所以**首个**需要用户权限的调用会拉起浏览器，要求你登录飞书
并授予应用第 2 步里的 scope。批准一次即可；lark-mcp 会在 `localhost:3000/callback` 回调处换取并缓存**用户
token**。此后 MCP 以**你的**token 身份访问，**你能看到的它就能读**，无需逐篇共享，token 过期前也不会
再提示。

> OAuth token 按机器缓存（macOS：`~/Library/Application Support/lark-mcp-nodejs/storage.json`），
> 且无法跨环境复制——换一台机器会要求你在浏览器里重新授权一次。应用只能看到**你本人**能看到的
> 内容；若某次读取文档报权限错误，请确认你自己的飞书账号对那篇文档或那个知识库空间有访问权。

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
