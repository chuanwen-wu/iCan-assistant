# iCan-assistant

English | [简体中文](./README_zh.md)

A single, copyable Claude Code plugin that turns Claude into an **office copilot** on
macOS. It bundles two backends and a router/orchestrator that decides which to use:

- **Local Apple Mail** (`scripts/mail.py`, via AppleScript) — read/search/send/reply,
  mark, move, delete.
- **Feishu / Lark** (the `lark` MCP server, bundled via `.mcp.json`) — docs/wiki,
  calendar, tasks, IM.

It also **orchestrates multi-step workflows** — e.g. *read several docs → summarize →
send an email + create a Feishu calendar event + create Feishu tasks* — by planning
gather → process → act and carrying results between steps.

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
- A Feishu/Lark app's credentials (for the lark MCP).

## Setup (one-time)

1. `cp .env.example .env` in this folder and fill in `FEISHU_APP_ID` /
   `FEISHU_APP_SECRET`. (`.env` is gitignored; the launcher auto-discovers it from
   `$CLAUDE_PLUGIN_ROOT/.env`, the plugin folder, or the host project's `.env`.)
2. Make sure `scripts/*.sh` / `scripts/*.py` are executable (`chmod +x`).

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

**Each user still does two things the plugin can't bundle:**

1. **Feishu credentials** — give the `lark` MCP server `FEISHU_APP_ID` /
   `FEISHU_APP_SECRET`. Don't put a `.env` inside the installed plugin folder: it
   lives under a versioned cache path and is wiped on upgrade. Use one of:
   - **Recommended** — keep a `.env` at a stable location and point the launcher at
     it: `export FEISHU_ENV_FILE=/abs/path/.env` (e.g. in your shell profile). `.env`
     is gitignored — never commit real keys.
   - **Or** export the variables directly:
     `export FEISHU_APP_ID=… FEISHU_APP_SECRET=…`.
2. **macOS Automation permission** — approve the prompt to let your terminal control
   "Mail" the first time email is used (System Settings → Privacy & Security →
   Automation). Email is macOS-only; Feishu features are cross-platform.

> **lark name clash:** if the project you install into already defines a `lark` MCP
> server in its own `.mcp.json` (this repo does), remove that one first so you don't
> end up with two `lark` servers. A fresh project needs only the plugin's `lark`.

## Alternative: plain folder copy (no plugin system)

The whole `iCan-assistant/` folder is self-contained — copy it anywhere and use it
without installing:

- **Email:** run `python3 scripts/mail.py …` directly (no Claude needed).
- **Feishu MCP:** add to the host project's `.mcp.json`:
  `{"mcpServers":{"lark":{"command":"bash","args":["/abs/path/to/iCan-assistant/scripts/lark-mcp.sh"]}}}`
  and provide a `.env`.
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
