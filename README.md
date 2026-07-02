# iCan-assistant

## 项目简介

该项目是一个 iCAN 办公助手，作为插件的形式被 AI Agent 集成（包括除了 Claude Code 之外的其他
agent），把 AI agent 变成你的 iCan 办公副手，接入你的文档/知识库、日历、任务、IM、多维表格、
电子表格、妙记、视频会议，以及邮件（iCan 中的邮件集成的是 21cn 邮件，非原生飞书邮件），可实现
复杂办公工作流编排。

典型场景，例如：

- **会前会后**：查今天的日程 → 找到对应会议的妙记/纪要 → 提炼待办 → 建飞书任务分给相关同事。
- **邮件转执行**：收到一封邮件 → 读懂内容 → 建日历日程 + 建飞书任务 + IM 通知相关同事，全程不用手动倒腾。
- **文档汇报**：读取多个飞书文档/知识库页面 → 总结成一封邮件发给老板，或整理进一份新文档。
- **表格周报**：从多维表格 / 电子表格里提取本周数据 → 汇总成周报 → 发到群里或存成文档。
- **收件箱整理**：批量查看未读邮件、按规则标记 / 归档 / 移动，早上五分钟清空收件箱。

在本仓库里，它以插件形式落地于 macOS，内置两套后端和一个负责决策的路由/编排器：
- **本机 Apple Mail**（`scripts/mail.py`，基于 AppleScript）—— 读取/搜索/发送/回复、标记、移动、删除。
- **iCan**（通过 **`lark-cli`** 与 `lark-*` 技能）—— 文档/知识库、日历、任务、IM、多维表格、电子表格、妙记、视频会议、审批、OKR、云盘等。用户只需授权一次，即可让AI Agent以**你本人身份**执行（不是机器人身份）。

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

飞书后端通过 **`lark-cli`** 访问飞书，以**你本人的用户身份**登录到一个自建应用下运行，不是机器人
身份。用哪个应用，先看下面第 0 步。

### 0. 先决定：借用现成应用，还是自己建一个

- **你和已经在用这套插件的人同属一家企业** —— 优先**找对方要 App ID + App Secret**，不用自己重新
  建应用、重新申请一遍权限。飞书自建应用本来就是企业级的，同企业成员共用同一个应用是官方支持的正常
  用法，只是要满足两点：
  1. 企业管理员要在该应用的「应用可用范围」里把你加进去（或设为全员可用），不然你后面 `auth login`
     授权会被拒绝；
  2. App Secret 是应用级凭证，请让对方走安全渠道给你（如 1Password / Keychain 共享），别用明文聊天
     传。拿到后自己在本机执行 `lark-cli config init` 填入即可——**登录仍然是各自独立的**，你跑一遍
     `auth login` 得到的是你自己的用户 token，不会用到对方的身份，也看不到对方的数据。
- **你要独立使用 / 不在同一家企业 / 想要完全隔离的环境** —— 自己新建一个自建应用，见下面「附：自建
  应用配置步骤」。

拿到 App ID（和需要的话，App Secret）后，继续下面的安装与登录步骤。

### 1. 安装 lark-cli

```
brew install lark-cli          # 或按 lark-cli 安装文档选择适合你系统的方式
lark-cli --version
```

### 2. 配置应用凭证

```
lark-cli config init            # 交互式填入 App ID + App Secret
```

用别人给的应用信息，还是自己新建的都在这一步填入。

### 3. 以本人身份登录并固定用户身份

```
lark-cli auth login            # 在该应用下以你本人身份做设备码登录
lark-cli config default-as user
lark-cli whoami                # 确认："identity": "user"，"tokenStatus": "ready"
```

`auth login` 会拉起设备码授权；完成后 `lark-cli` 持有**你的**用户 token 并以你的身份行事——
**你能看到的它就能读/操作**，无需逐篇共享文档。`config default-as user` 让用户身份成为每次调用
的默认身份。

### 4. 开通 API 权限（scope）

> 如果是借用同事已经配好的应用，且对方已经开通了你要用的面，这一步可以跳过；缺哪个权限用哪个再补。

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

### 附：自建应用配置步骤（如果你要自己新建）

1. 打开 <https://open.feishu.cn/app>（国际版 Lark 用 <https://open.larksuite.com/>），用你的
   企业账号登录开发者后台。
2. 点「创建企业自建应用」，填应用名称、描述、图标，创建即可，不用等审核。
3. 进入应用详情页 →「凭证与基础信息」，拿到 **App ID** 和 **App Secret**（Secret 只在需要时点开
   查看/重置，注意保管）。
4. 「权限管理」里按上面表格搜索并开通需要的 scope；要写操作的面记得读、写权限都开。
5. 「版本管理与发布」创建一个版本、勾选本次开通的权限、提交发布——企业管理员审核通过后权限才真正
   生效，之后新增权限同理需要发新版本。
6. 「应用可用范围」里确认自己（以及后续要用这个应用的同事）在可见范围内；默认通常只有创建者可见，
   给团队用的话建议改成部门可见或全员可见，省得每次加人都要回来改。
7. 回到本机，`lark-cli config init` 填入这个 App ID / App Secret，接着走上面「登录」步骤。

（飞书开发者后台偶尔会调整菜单文案，若某一项找不到，按关键词在后台搜索栏搜一下即可。）

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
