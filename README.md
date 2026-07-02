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
- **iCan / 飞书**（通过 **`lark-cli`** 与 `lark-*` 技能）—— 邮件之外的全部面，另含审批、OKR、云盘等。用户只需授权一次，即可让 AI Agent 以**你本人身份**执行（不是机器人身份）。

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

- 装有 Mail.app 的 macOS（邮件功能仅限 macOS；飞书功能跨平台可用）—— 首次使用邮件时，批准让
  终端控制 “Mail” 的自动化（Automation）权限弹窗（系统设置 → 隐私与安全性 → 自动化）。
  无需完全磁盘访问权限。
- Python 3（用于 `mail.py`）。
- **`lark-cli`**（飞书侧）—— 安装、配置与登录见 [飞书配置](#飞书配置lark-cli)。它内置的
  `lark-*` 技能驱动全部飞书操作。

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

安装后，`office-router` / `local-email` 技能与 `/office`、`/email` 命令会自动加载。剩下的
一次性配置只有两件：批准 macOS 自动化权限弹窗（见 [环境要求](#环境要求)），以及配置
`lark-cli`（见下一节）。

## 飞书配置（lark-cli）

飞书后端通过 **`lark-cli`** 访问飞书，以**你本人的用户身份**登录到一个企业自建应用下运行，
不是机器人身份。

### 1. 飞书应用

**推荐使用已经创建好的企业应用「iCan Assistant」**——权限已配好，不用自己建应用、申请权限：

- 找应用管理员 **Kennethwu** 要 **App ID + App Secret**，同时请他把你加入该应用的
  「应用可用范围」（使用者），否则后面 `auth login` 授权会被拒绝。
- App Secret 是应用级凭证，请让对方走安全渠道给你（如 1Password / Keychain 共享）。登录是
  各自独立的——你 `auth login` 得到的是你自己的用户 token，不会用到对方的身份，也看不到对方
  的数据。

同企业成员共用同一个自建应用是飞书官方支持的正常用法。如果你不在同一家企业、要独立使用，或想要
完全隔离的环境，见下面第 3 步从 0 创建自己的应用。

### 2. 安装配置 lark-cli

```
brew install lark-cli             # 或按 lark-cli 安装文档选择适合你系统的方式
lark-cli config init              # 交互式填入第 1 步拿到的 App ID + App Secret
lark-cli auth login               # 在该应用下以你本人身份做设备码登录
lark-cli config default-as user   # 让用户身份成为每次调用的默认身份
lark-cli whoami                   # 确认："identity": "user"，"tokenStatus": "ready"
```

登录后 `lark-cli` 持有**你的**用户 token 并以你的身份行事——**你能看到的它就能读/操作**，
无需逐篇把文档共享给应用。

### 3. 从 0 开始配置飞书应用

> 如果第 1 步已经使用预先配置好的应用（iCan Assistant），这一步可以跳过。这一步适用于想从 0
> 开始创建和配置飞书应用的人。

1. 打开 <https://open.feishu.cn/app>（国际版 Lark 用 <https://open.larksuite.com/>），用你的
   企业账号登录开发者后台。
2. 点「创建企业自建应用」，填应用名称、描述、图标，创建即可，不用等审核。
3. 进入应用详情页 →「凭证与基础信息」，拿到 **App ID** 和 **App Secret**（Secret 只在需要时点开
   查看/重置，注意保管）。
4. 「权限管理」里按下面表格搜索并开通需要的 scope；要写操作的面记得**读、写权限都开**：

   | 面 | 代表性 scope |
   |---|---|
   | IM / 消息 | `im:message`、`im:chat`、`im:resource` |
   | 日历 | `calendar:calendar`（含日程创建/管理） |
   | 云文档 / 知识库 / 云盘 | `docx:document`、`wiki:wiki`、`drive:drive`（只读用 `:readonly` 变体） |
   | 任务 | `task:task` |
   | 多维表格 / 电子表格 | `bitable:app`、`sheets:spreadsheet` |
   | 妙记 / 视频会议 | `minutes:minutes`、`vc:*`（读） |
   | 通讯录（按 id 解析用户） | `contact:*:readonly` |

   若某次调用报权限错误，补上缺失的 scope，必要时重新发布版本，再重试。
5. 「版本管理与发布」创建一个版本、勾选本次开通的权限、提交发布——企业管理员审核通过后权限才真正
   生效，之后新增权限同理需要发新版本。
6. 「应用可用范围」里确认自己（以及后续要用这个应用的同事）在可见范围内；默认通常只有创建者可见，
   给团队用的话建议改成部门可见或全员可见，省得每次加人都要回来改。
7. 回到本机，走上面第 2 步：`lark-cli config init` 填入这个 App ID / App Secret，然后登录。

（飞书开发者后台偶尔会调整菜单文案，若某一项找不到，按关键词在后台搜索栏搜一下即可。）

## 替代方案：纯目录复制（不走插件系统）

整个 `iCan-assistant/` 目录是自包含的——复制到任何位置都能直接用，无需安装：

- **邮件：** 直接运行 `python3 scripts/mail.py …`（无需 Claude）：

  ```bash
  python3 scripts/mail.py --help                  # 全部子命令：accounts/mailboxes/list/search/
                                                  #   read/unread-count/send/reply/mark/move/delete
  python3 scripts/mail.py list --limit 10 --unread
  python3 scripts/mail.py list --limit 10 --json  # 机器可读的 JSON 输出
  ```

- **飞书：** 确保已安装并登录 `lark-cli`（见上面步骤），用 `lark-cli <domain> …` 驱动
  （例如 `lark-cli calendar +agenda`）。
- **路由/编排逻辑：** 不安装时技能不会自动触发——把
  `skills/office-router/SKILL.md` 里的关键规则复制进项目的 `CLAUDE.md`/`AGENTS.md`，或手动调用技能。

## 使用

- `/office <请求>` —— 跨邮件 + 飞书的路由 + 多步编排。
- `/email <请求>` —— 仅邮件。
- 若与其他插件的同名命令冲突，用完整写法：`/ican-assistant:office`、`/ican-assistant:email`。
- 或直接自然语言提问（“看下我未读邮件”、“总结这几个飞书文档并发给老板”）——
  `office-router` 技能会在邮件/飞书/办公工作流类请求上自动触发。

## 安全

发送/回复邮件、发 IM 消息、创建/修改日历事件或任务、删除/移动邮件、共享文档，都是真实的、
对外的操作。技能会指示 Claude 在执行前确认收件人/标题/正文/时间、遵守 `lark-cli` 的风险分级
（绝不自动确认 `high-risk-write`），并在意图不明时优先把邮件存为**草稿**。如果你改编这些技能，
请保留该行为。
