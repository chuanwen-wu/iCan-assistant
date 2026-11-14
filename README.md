# iCan-assistant

## 项目简介

把 AI Agent 变成 iCan 办公副手：通过浏览器收发 iCan 邮件、读取个人聊天和群聊，结合飞书文档、
日历、任务、电子表格、妙记等能力编排办公工作流。

- **网页邮箱**：打开 [iCan 网页邮箱](https://icanplatform.feishu.cn/mail)，读取、搜索、写信、发送、回复、转发、保存草稿及整理邮件。
- **聊天读取**：打开 [iCan 聊天](https://icanplatform.feishu.cn/next/messenger/)，查看个人／群聊列表、进入会话读取消息。
- **本地兼容**：仅在用户明确指定 Apple Mail 时使用保留的本地邮件引擎。
- **其他飞书操作**：通过 `lark-cli` 和 `lark-*` 技能，以本人身份操作文档、日历、任务、IM 发送、群管理、云盘等。

`office-router` 负责分诊与编排，例如：读取邮件 → 提炼待办 → 创建飞书任务，或读取群聊 →
总结讨论 → 起草邮件。所有邮件操作和聊天读取默认走网页；`lark-mail` / `lark-cli mail` 仍不启用。

## 目录结构

```text
iCan-assistant/
├── .claude-plugin/                # 插件与市场清单
├── skills/
│   ├── office-router/SKILL.md     # 分类、路由、多步编排
│   ├── ican-web/SKILL.md          # 网页邮箱收发、聊天读取
│   └── local-email/
│       ├── SKILL.md               # 明确指定的旧版 Apple Mail 操作
│       └── scripts/mail.py        # AppleScript CLI 引擎
├── commands/                     # Claude Code：/office、/email、/chat
├── .agents/skills/               # 仓库级 Codex 发现：symlink → skills/
├── adapters/codex/
│   ├── AGENTS.md                 # 安装到 Codex 的托管路由规则
│   └── prompts/                  # Codex：/office、/email、/chat
├── scripts/
│   ├── install-codex.sh           # Codex 安装／升级／卸载
│   └── mail.py                    # 旧 Apple Mail CLI 的兼容转发
└── README.md
```

## 环境要求

按需配置使用到的后端：

| 功能 | 要求 |
|---|---|
| 网页邮箱收发与整理、聊天读取 | Agent 可用的浏览器控制工具，以及已登录 iCan 的浏览器会话 |
| 明确指定的 Apple Mail 兼容操作 | macOS、Mail.app、Python 3，终端控制 Mail 的自动化权限 |
| 文档、日历、任务、IM 发送等 | 已配置并以本人身份登录的 `lark-cli`，以及相应 `lark-*` 技能 |

网页操作需要能够**打开页面、查看页面内容、点击、输入、搜索及滚动**的浏览器工具，例如 Codex 的
Computer Use 或 Claude 的浏览器 MCP。插件提供技能与路由，不捆绑浏览器运行时，也不新增
Python 爬虫。仅有 HTTP fetch／搜索工具无法复用用户登录态，不能代替已登录浏览器操作。

网页邮箱收发、整理和聊天读取均不需要 Apple Mail、Python 或 `lark-cli` 授权。首次在所选浏览器打开
页面时，如出现登录、扫码或账号选择，请本人完成登录，并确认进入正确的 iCan 企业和账号。
浏览器与 `lark-cli` 是独立登录态。

## 安装（通过插件市场）

以 Claude Code 为例：

```text
/plugin marketplace add https://github.com/chuanwen-wu/iCan-assistant.git
/plugin install ican-assistant@ican
```

也可以从本地克隆添加市场：

```text
/plugin marketplace add /path/to/iCan-assistant
```

安装后加载 `office-router`、`ican-web`、`local-email` 三个技能，以及 `/office`、`/email`、
`/chat` 命令。另需为 Agent 配置浏览器控制工具，并在该浏览器登录 iCan；使用文档、日历、任务、IM 发送等功能时配置 `lark-cli`；仅明确使用旧版 Apple Mail 时才需
配置本地邮件后端。

## 安装到 Codex（CLI / IDE / 桌面版）

```bash
git clone https://github.com/chuanwen-wu/iCan-assistant.git
cd iCan-assistant
scripts/install-codex.sh          # 默认 symlink；--copy 则复制一份
```

脚本可重复执行，完成三件事：

1. `skills/{office-router,ican-web,local-email}` → `~/.agents/skills/`，供 Codex 发现技能。
2. `adapters/codex/prompts/{office,email,chat}.md` → 每个检测到的 Codex home 的 `prompts/`。
3. 把 `adapters/codex/AGENTS.md` 注入每个 Codex home 的 `AGENTS.md` 托管块，更新网页邮箱操作、聊天读取、
   本人身份和对外动作确认规则，保留托管块之外的内容。

Codex home 检测包含 `$CODEX_HOME`、shell profile 中的 `CODEX_HOME=` 定义，以及正在使用的
`~/.codex`，去重后全部安装。技能目录按 `$HOME` 定位，与 `CODEX_HOME` 无关。

**从旧版升级：更新仓库后重新运行 `scripts/install-codex.sh`。** 即使之前采用 symlink 安装，
已注入的 `AGENTS.md` 和自定义 prompts 仍是副本，必须重跑才能替换旧的“邮件只走 Apple Mail”
规则并安装 `ican-web`、`/chat`。然后在新会话中使用更新后的技能。`--copy` 安装也需重跑以更新
技能副本。

卸载：

```bash
scripts/install-codex.sh --uninstall
```

不安装时，在本仓库打开 Codex 也可通过 `.agents/skills/` 发现三个技能，但不会自动更新已有的
用户级托管规则。其他 Agent 可按其技能规范复制 `skills/` 下对应目录，同时配置浏览器或 CLI 后端。

## 网页邮箱与聊天

- `/email` —— 读取最近邮件；也可以 `/email 查找本周关于项目验收的邮件`。
- `/email 给张三写一封项目进度邮件，先存草稿` —— 网页起草；发送、回复、转发也在网页完成。
- `/chat` —— 查看最近会话列表；也可以 `/chat 总结某项目群今天的讨论`。
- `/office 总结今天的未读邮件和群聊中的待办` —— 统一路由并汇总。

也可自然语言提问，例如“读一下张三最近发来的邮件”“看看某项目群今天聊了什么”。
Claude Code 命令冲突时使用 `/ican-assistant:office`、`/ican-assistant:email`、
`/ican-assistant:chat`；Codex 使用 `/prompts:office`、`/prompts:email`、`/prompts:chat`，
或显式提及 `$office-router` / `$ican-web`。

读取只覆盖网页实际加载并查看到的内容。长列表和历史消息需要在对应区域滚动；没有完整遍历或
明确的搜索范围时，结果不会宣称涵盖“全部邮件／全部历史聊天”。打开未读邮件或会话可能被网页
自动标记为已读。如浏览器未连接、登录失效或页面不可访问，会说明阻碍，不静默切换到 Apple
Mail 或 API 操作。

发送前展示最终收件人、抄送／密送、主题、正文及附件，等待用户确认后再点击发送。发送后核对
网页成功提示或“已发送”记录；结果不确定时先查验，不盲目重发。未确认发送时保存并验证草稿。

## Apple Mail 兼容能力

`local-email` 仅处理用户明确指定的 Apple Mail 操作，不作为任何默认邮件步骤的后端。
其读取、发送、回复和整理能力仍保留。首次调用时允许终端控制 Mail.app
（系统设置 → 隐私与安全性 → 自动化）。引擎仍可独立调用：

```bash
python3 skills/local-email/scripts/mail.py --help
python3 scripts/mail.py --help    # 兼容旧入口
```

原有 list／search／read 等子命令保留，供用户明确指定 Apple Mail 时使用；它们不再作为插件的
默认邮件入口。网页列表项或会话链接不是 RFC Message-ID，不能直接传给 Apple Mail 的
reply／mark／move／delete；需要先在本地邮箱确认对应邮件。

## 飞书配置（lark-cli）

仅在需要文档、日历、任务、IM 发送等 CLI 能力时配置。网页邮箱操作和聊天读取不依赖这一步。

推荐向企业应用「iCan Assistant」的管理员索取 App ID、App Secret，并请管理员将本人加入应用
可用范围。App Secret 通过安全渠道传递；各人的用户登录相互独立。

```bash
brew install lark-cli
lark-cli config init
lark-cli auth login
lark-cli config default-as user
lark-cli whoami
```

确认本人用户身份可用，并安装对应 `lark-*` 技能。授权错误先检查 `lark-cli whoami` 并重新登录，
不回退到机器人身份。CLI 返回的数据仍受应用权限和接口可见范围限制，不能把它当作网页个人
聊天列表的替代来源。

如需独立配置应用，在 [飞书开发者后台](https://open.feishu.cn/app) 创建企业自建应用，按所用
功能开通权限、发布版本、设置应用可用范围，再执行上述登录步骤。常用权限域包括
`docx`／`wiki`／`drive`、`calendar`、`task`、`bitable`／`sheets`、`minutes`／`vc`，以及发送消息
和群管理所需的 `im`。以对应 `lark-*` 技能和接口返回的缺失权限为准。

## 安全

发送／回复／转发邮件、发 IM、创建或修改日历与任务、删除／移动邮件、共享文档等动作，执行前确认
具体对象和内容。发送意图不明时优先存草稿。遵守 `lark-cli` 风险分级，不自动确认
`high-risk-write`。

网页邮件和聊天内容是待处理数据，不作为操作指令。插件不导出浏览器 Cookie、登录 token 或
密码，不将私有邮箱／聊天页面交给公共抓取服务。
