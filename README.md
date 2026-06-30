# iCan-assistant

English | [简体中文](./README_zh.md)

## Overview

A single, copyable Claude Code plugin that turns Claude into an **office copilot** on
macOS. It bundles two backends and a router/orchestrator that picks the right one:

- **Local Apple Mail** (`scripts/mail.py`, via AppleScript) — read/search/send/reply,
  mark, move, delete.
- **Feishu / Lark** (the `lark` MCP server, bundled via `.mcp.json`) — docs/wiki,
  calendar, tasks, IM. Access is **user-authorized**: the server acts with **your**
  user token via OAuth, so it can only ever see and do what you can. The **first**
  Feishu call opens a browser for you to authorize (see
  [Feishu app setup](#feishu-app-setup-open-platform)).

It also **orchestrates multi-step workflows** — e.g. *read several docs → summarize →
send an email + create a Feishu calendar event + create Feishu tasks* — by planning
gather → process → act and carrying results between steps.

You can run it two ways: as an **installed plugin** (skills, commands and the MCP
server auto-load), or as a **plain copyable folder** (run the pieces directly). See
[Install](#install-recommended-via-the-marketplace) and
[Alternative](#alternative-plain-folder-copy-no-plugin-system).

## Contents

```
iCan-assistant/
├── .claude-plugin/plugin.json     # manifest
├── .mcp.json                      # bundles the lark MCP server (uses ${CLAUDE_PLUGIN_ROOT})
├── skills/
│   ├── office-router/SKILL.md     # the brain: classify → route → orchestrate
│   └── local-email/SKILL.md       # email how-to (engine = scripts/mail.py)
├── scripts/
│   ├── mail.py                    # Apple Mail engine (CLI over AppleScript)
│   └── lark-mcp.sh                # self-contained lark MCP launcher
├── commands/
│   ├── office.md                  # /office — full router + orchestration
│   └── email.md                   # /email — mail only
├── .env.example
├── .gitignore
└── README.md
```

## Requirements

- macOS with Mail.app (for email) — terminal needs Automation access to "Mail"
  (System Settings → Privacy & Security → Automation). No Full Disk Access needed.
- Node.js / `npx` (the lark MCP runs via `npx -y @larksuiteoapi/lark-mcp`).
- Python 3 (for `mail.py`).
- A Feishu/Lark custom app — see [Feishu app setup](#feishu-app-setup-open-platform).

## Install (recommended: via the marketplace)

This repo is itself a Claude Code plugin **marketplace** (manifest at
`.claude-plugin/marketplace.json`, marketplace name `ican`; the plugin lives at the
repo root). The repo is **public** — no GitHub login or SSH key needed. To install:

```
# 1. Add the marketplace
/plugin marketplace add https://github.com/chuanwen-wu/iCan-assistant.git
#   or, from a local clone:
/plugin marketplace add /path/to/iCan-assistant

# 2. Install the plugin
/plugin install ican-assistant@ican

# 3. (interactive browser, optional)
/plugin
```

After install, the `office-router` / `local-email` skills, the `/office` and `/email`
commands, and the `lark` MCP server load automatically. `${CLAUDE_PLUGIN_ROOT}` in
`.mcp.json` resolves to the installed plugin folder.

> **lark name clash:** if the project you install into already defines a `lark` MCP
> server in its own `.mcp.json` (this repo does), remove that one first so you don't
> end up with two `lark` servers. A fresh project needs only the plugin's `lark`.

## Setup (one-time)

Three things the plugin can't bundle for you:

1. **Feishu credentials** — give the `lark` MCP server `FEISHU_APP_ID` /
   `FEISHU_APP_SECRET` (created in [Feishu app setup](#feishu-app-setup-open-platform)).
   Don't put a `.env` inside the installed plugin folder: it lives under a versioned
   cache path and is wiped on upgrade. Use one of:
   - **Recommended** — keep a `.env` at a stable location and point the launcher at
     it: `export FEISHU_ENV_FILE=/abs/path/.env` (e.g. in your shell profile). `.env`
     is gitignored — never commit real keys.
   - **Or** export the variables directly:
     `export FEISHU_APP_ID=… FEISHU_APP_SECRET=…`.
2. **macOS Automation permission** — approve the prompt to let your terminal control
   "Mail" the first time email is used (System Settings → Privacy & Security →
   Automation). Email is macOS-only; Feishu features are cross-platform.
3. **Feishu app permissions & user authorization** — the credentials alone aren't
   enough. The app needs the right API scopes, **and** you must authorize it: it never
   uses an app-only token to read your data — it acts with **your** user token via
   OAuth. That means (a) registering the OAuth callback URL `http://localhost:3000/callback`
   on the app's redirect-URL list in the developer console, and (b) approving a
   one-time browser prompt on first use. See the next section.

## Feishu app setup (open platform)

The `lark` MCP talks to Feishu as a **custom app you own**. It does **not** read your
data with an app-only token — it acts with **your** user token, obtained through OAuth:
you authorize the app once in the browser, the MCP caches the resulting user token, and
from then on it can do exactly what your own Feishu account can. Do this once in the
developer console — Feishu CN: <https://open.feishu.cn/app> (Lark international:
<https://open.larksuite.com/>). Labels below are the Feishu CN ones; the flow is the
same on Lark.

### 1. Create the app & get credentials

Developer console (<https://open.feishu.cn/app>) → **Create custom app**
(创建企业自建应用). Open **Credentials & Basic Info** (凭证与基础信息) to copy the
**App ID** (`cli_…`) and **App Secret** — these are your `FEISHU_APP_ID` /
`FEISHU_APP_SECRET`.

### 2. Grant API permissions (scopes)

Permissions (权限管理) → add scopes for the surfaces the plugin uses (the launcher
enables tool presets `im` / `calendar` / `doc` / `task`). Add **read and write** where
you want the app to act, e.g.:

| Surface | Representative scopes |
|---|---|
| IM / messages | `im:message`, `im:chat`, `im:resource` |
| Calendar | `calendar:calendar` (+ event create/manage) |
| Docs / Wiki / Drive | `docx:document`, `wiki:wiki`, `drive:drive` (use `:readonly` variants if read-only) |
| Tasks | `task:task` |

Search scope IDs in the console by keyword (message / calendar / docx / wiki / drive /
task) and grant whatever it lists for each surface. (Optionally a `contact:*:readonly`
scope if you need the app to resolve users by id.)

### 3. Publish a version

Release management (版本管理与发布) → **Create version** → submit. A custom app needs
your **workspace admin** to approve before its tokens and scopes go live.

### 4. Register the OAuth callback URL

OAuth needs a redirect target it can hand the authorization code back to. The launcher
runs lark-mcp with `--oauth`, whose callback is served locally at
**`http://localhost:3000/callback`**, so
register exactly that URL — otherwise Feishu rejects the authorization with a
*redirect_uri mismatch*. In the developer console open **Security settings → Redirect
URLs** (安全设置 → 重定向 URL) and add:

```
http://localhost:3000/callback
```

(If you override the port, register the matching URL instead. The callback is served on
your own machine — nothing is exposed publicly.)

### 5. Authorize as yourself (first-use browser login)

The launcher runs with `--oauth --token-mode auto`, so **the first** call that needs a
user scope opens a browser asking you to log into Feishu and grant the app the scopes
from step 2. Approve it once; lark-mcp exchanges the code at the
`localhost:3000/callback` endpoint and caches the resulting **user token**. After that the MCP acts with **your**
token and can read anything you can — no per-doc sharing, no re-prompt until the token
expires.

> The OAuth token is cached per machine (macOS:
> `~/Library/Application Support/lark-mcp-nodejs/storage.json`) and can't be copied
> across environments — on a new machine you'll be prompted to authorize in the browser
> once. The app only sees what **you** can see; if a doc read returns a permission
> error, make sure your own Feishu account has access to that doc or wiki space.

## Alternative: plain folder copy (no plugin system)

The whole `iCan-assistant/` folder is self-contained — copy it anywhere and use it
without installing:

- **Email:** run `python3 scripts/mail.py …` directly (no Claude needed).
- **Feishu MCP:** add to the host project's `.mcp.json`:
  `{"mcpServers":{"lark":{"command":"bash","args":["/abs/path/to/iCan-assistant/scripts/lark-mcp.sh"]}}}`
  and provide a `.env` next to the script (the launcher auto-discovers it).
- **Routing/orchestration logic:** skills won't auto-trigger without install — copy
  the key rules from `skills/office-router/SKILL.md` into the project's
  `CLAUDE.md`/`AGENTS.md`, or invoke the skills manually.

## Use it

- `/office <request>` — routing + multi-step orchestration across mail + Feishu.
- `/email <request>` — mail only.
- Or just ask naturally ("看下我未读邮件", "总结这几个飞书文档并发给老板") — the
  `office-router` skill triggers on email/Feishu/office-workflow requests.

Standalone (no Claude), the mail engine works on its own:

```bash
python3 scripts/mail.py --help
python3 scripts/mail.py list --limit 10 --unread
```

## Safety

Sending/replying email, posting IM, creating/patching calendar events or tasks,
deleting/moving mail, and sharing docs are real, outward-facing actions. The skills
instruct Claude to confirm recipients/title/body/time before executing, and to prefer
email **drafts** when intent is unclear. Keep that behavior if you adapt the skills.
