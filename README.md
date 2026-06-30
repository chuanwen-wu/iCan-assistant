# iCan-assistant

English | [简体中文](./README_zh.md)

## Overview

A single, copyable Claude Code plugin that turns Claude into an **office copilot** on
macOS. It bundles two backends and a router/orchestrator that picks the right one:

- **Local Apple Mail** (`scripts/mail.py`, via AppleScript) — read/search/send/reply,
  mark, move, delete.
- **Feishu / Lark** (via **`lark-cli`** and the `lark-*` skills) — docs/wiki, calendar,
  tasks, IM, 多维表格 (bitable), 电子表格 (sheets), 妙记 (minutes), VC, approval, OKR,
  drive, and more. Feishu actions run as **your own identity** (not a bot).

It also **orchestrates multi-step workflows** — e.g. *read several docs → summarize →
send an email + create a Feishu calendar event + create Feishu tasks* — by planning
gather → process → act and carrying results between steps.

You can run it two ways: as an **installed plugin** (skills and commands auto-load), or
as a **plain copyable folder** (run the pieces directly). See
[Install](#install-recommended-via-the-marketplace) and
[Alternative](#alternative-plain-folder-copy-no-plugin-system).

## Contents

```
iCan-assistant/
├── .claude-plugin/plugin.json     # manifest
├── skills/
│   ├── office-router/SKILL.md     # the brain: classify → route → orchestrate
│   └── local-email/SKILL.md       # email how-to (engine = scripts/mail.py)
├── scripts/
│   └── mail.py                    # Apple Mail engine (CLI over AppleScript)
├── commands/
│   ├── office.md                  # /office — full router + orchestration
│   └── email.md                   # /email — mail only
├── .gitignore
└── README.md
```

## Requirements

- macOS with Mail.app (for email) — terminal needs Automation access to "Mail"
  (System Settings → Privacy & Security → Automation). No Full Disk Access needed.
- Python 3 (for `mail.py`).
- **`lark-cli`** for the Feishu side — install it and log in once (see
  [Feishu setup](#feishu-setup-lark-cli)). The Feishu `lark-*` skills it ships drive
  all docs/calendar/tasks/IM/bitable/etc. operations.

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

After install, the `office-router` / `local-email` skills and the `/office` and
`/email` commands load automatically. The Feishu backend uses your host's `lark-cli`
install (the plugin no longer bundles an MCP server).

## Setup (one-time)

Three things the plugin can't bundle for you:

1. **`lark-cli` + Feishu login** — see [Feishu setup](#feishu-setup-lark-cli). Install
   `lark-cli`, log in as yourself, and pin user identity.
2. **macOS Automation permission** — approve the prompt to let your terminal control
   "Mail" the first time email is used (System Settings → Privacy & Security →
   Automation). Email is macOS-only; Feishu features are cross-platform.
3. **Feishu app permissions** — the login alone isn't enough; the app needs the right
   API scopes for the surfaces you use. See the next section.

## Feishu setup (lark-cli)

The Feishu backend talks to Feishu through **`lark-cli`**, acting with **your own user
identity** under a custom app you own. The app configuration is unchanged from the
existing setup (same App ID `cli_a97286141d785bc4`); you just log in as the user.

### 1. Install lark-cli

```
brew install lark-cli          # or follow the lark-cli install docs for your OS
lark-cli --version
```

### 2. Log in as yourself and pin user identity

```
lark-cli auth login            # device-flow login under the app, as you
lark-cli config default-as user
lark-cli whoami                # confirm: "identity": "user", "tokenStatus": "ready"
```

`auth login` opens a device-flow authorization; after it completes, `lark-cli` holds
**your** user token and acts as you — it can read/act on anything you can, with no
per-doc sharing. `config default-as user` makes user identity the default for every
call.

### 3. Grant API permissions (scopes)

In the developer console (Feishu CN: <https://open.feishu.cn/app>, Lark international:
<https://open.larksuite.com/>) → **Permissions** (权限管理) → add scopes for the
surfaces you use. Add **read and write** where you want to act, e.g.:

| Surface | Representative scopes |
|---|---|
| IM / messages | `im:message`, `im:chat`, `im:resource` |
| Calendar | `calendar:calendar` (+ event create/manage) |
| Docs / Wiki / Drive | `docx:document`, `wiki:wiki`, `drive:drive` (use `:readonly` variants if read-only) |
| Tasks | `task:task` |
| 多维表格 / Sheets | `bitable:app`, `sheets:spreadsheet` |
| 妙记 / VC | `minutes:minutes`, `vc:*` (read) |
| Contacts (resolve users by id) | `contact:*:readonly` |

Search scope IDs in the console by keyword and grant whatever each surface lists. If a
call returns a permission error, add the missing scope, re-publish if required, and
retry. Because you act as yourself, document access follows **your** own permissions —
no need to share docs to a bot.

## Alternative: plain folder copy (no plugin system)

The whole `iCan-assistant/` folder is self-contained — copy it anywhere and use it
without installing:

- **Email:** run `python3 scripts/mail.py …` directly (no Claude needed).
- **Feishu:** ensure `lark-cli` is installed and logged in (steps above); drive it with
  `lark-cli <domain> …` (e.g. `lark-cli calendar +agenda`).
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
instruct Claude to confirm recipients/title/body/time before executing, to respect
`lark-cli` risk tiers (never auto-confirm a `high-risk-write`), and to prefer email
**drafts** when intent is unclear. Keep that behavior if you adapt the skills.
