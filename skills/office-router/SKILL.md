---
name: office-router
description: Entry point and orchestrator for office tasks on this Mac. Use whenever the user asks anything about email or Feishu/Lark (邮件/收件箱/Apple Mail, 飞书/Lark 文档/云文档/wiki, 日历/会议, 任务/待办/todo, 群/消息/发消息, 多维表格/电子表格, 妙记/会议纪要), OR asks for a multi-step office workflow (e.g. read documents then summarize then send an email / create a calendar event / create tasks). This skill classifies the request, routes each part to local Apple Mail or to the Feishu/Lark backend (lark-cli + the lark-* skills), and orchestrates multi-step plans end to end.
---

# Office Router & Orchestrator

You coordinate two backends to get office work done on this Mac:

| Backend | How to call it | Use for |
|---|---|---|
| **Local Apple Mail** | `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/mail.py …` (see the `local-email` skill) | reading/searching/sending/replying email, inbox triage |
| **Feishu / Lark** | **`lark-cli`** + the `lark-*` skills (see the skill map below) | docs/wiki, calendar, tasks, IM/chat, 多维表格, 电子表格, 妙记, VC, 审批, OKR, drive… |

This router is a **dispatcher**: it classifies the request and hands each Feishu
intent to the matching `lark-*` skill, which knows the exact `lark-cli` commands.
Don't re-implement `lark-cli` usage here — delegate.

## Feishu identity — act as the user

All Feishu actions run as **the user's own identity** (not the bot). The app
configuration is unchanged — it's the same custom app `cli_a97286141d785bc4`; only
the acting identity is the logged-in user.

- Default identity is pinned with `lark-cli config default-as user`.
- This requires a one-time `lark-cli auth login` (device-flow) under that app. If a
  Feishu call fails with an auth/identity error, check `lark-cli whoami` — if
  `identity` isn't `user` or no user is logged in, tell the user to run
  `lark-cli auth login` (and, if needed, `lark-cli config default-as user`). Do not
  silently fall back to bot identity.

## Step 1 — Classify the request

Split the user request into one or more **intents**. Map keywords/scenarios:

- **Email** (→ local-email, **always**): 邮件, 收件箱, 未读, Apple Mail, 发邮件, 回复,
  收到的…, an `@`-address recipient, "send/reply/forward", checking what someone emailed.
  **All email/mail intents go to local Apple Mail — including 飞书邮箱 / Feishu Mail.**
  Feishu Mail (`lark-mail`) is **disabled** in this plugin; never route any mail
  request to `lark-cli mail` / `lark-mail`, even if the user says 飞书邮箱. The only
  Feishu surface that is *not* a mail intent is IM/群聊 (→ lark-im).
- **Feishu docs** (→ lark-doc / lark-wiki): 飞书文档/云文档/docx, wiki/知识库, a
  `feishu.cn/.../docx/…` or `/wiki/…` link, "读文档/总结文档".
- **Feishu calendar** (→ lark-calendar): 日历, 日程, 会议, 约时间, freebusy, "安排/创建会议".
- **Feishu tasks** (→ lark-task): 任务, 待办, todo, 清单, "建任务/提醒".
- **Feishu IM** (→ lark-im): 群, 群聊, 发消息给…, chat, 通知某人.
- **多维表格 / Base** (→ lark-base): 多维表格, bitable, a `/base/…` link, 建表/字段/记录.
- **电子表格 / Sheets** (→ lark-sheets): 电子表格, sheet, 表格读写/统计/图表.
- **妙记 / 会议纪要** (→ lark-minutes / lark-vc): 妙记, 逐字稿, 会议纪要, 录音转写,
  past meeting summaries.
- **Drive / 云盘** (→ lark-drive): 云盘, 文件夹, 上传/下载/移动文件, 文件导入.

Other Feishu surfaces have their own skills too (lark-approval, lark-okr,
lark-slides, lark-markdown, lark-whiteboard, lark-attendance,
lark-contact …). Route to whichever matches; fall back to the relevant skill's
`lark-cli <domain> --help` if unsure. (`lark-mail` is intentionally excluded —
mail always goes to local Apple Mail, see the Email intent above.)

Default folder for Feishu docs when the user gives no link (project convention):
`https://icanplatform.feishu.cn/drive/folder/RtWofl1yalrpKYd9tS1c8STnnqd`.

If an intent is genuinely ambiguous (e.g. "通知团队" could be email or a Feishu
group), ask one short clarifying question; otherwise pick the obvious backend and
proceed.

## Step 2 — Route (skill map)

**Email** — delegate to the `local-email` skill. Common ones:
`mail.py list --unread`, `mail.py search "…"`, `mail.py read "<id>"`,
`mail.py send --to … --subject … --body …` (use `--draft` when intent to send is
unclear).

**Feishu** — delegate to the matching `lark-*` skill; each one drives `lark-cli`:

| Intent | Skill | Entry point |
|---|---|---|
| Docs / wiki read·edit | `lark-doc`, `lark-wiki` | `lark-cli docs …`, `lark-cli wiki …` |
| Calendar / 会议 | `lark-calendar` | `lark-cli calendar +agenda`, `… calendar event …` |
| Tasks / 待办 | `lark-task` | `lark-cli task …` |
| IM / 群·消息 | `lark-im` | `lark-cli im …` |
| 多维表格 | `lark-base` | `lark-cli base …` |
| 电子表格 | `lark-sheets` | `lark-cli sheets …` |
| 妙记 / 逐字稿 | `lark-minutes` | `lark-cli minutes …` |
| 历史会议 / 纪要 | `lark-vc` | `lark-cli vc …` |
| 云盘 / 文件 | `lark-drive` | `lark-cli drive …` |

Prefer a skill's high-level `+shortcut` over raw API commands. For any surface not
listed, browse with `lark-cli <domain> --help`, inspect a call with
`lark-cli schema <service.resource.method>`, and use `lark-cli api <METHOD> <path>`
as the raw escape hatch when no typed command fits.

`lark-cli` risk tiers apply: `read` is safe; `write` is an outward action (confirm —
see Safety); `high-risk-write` additionally needs `--yes`, only after the user OKs.

## Step 3 — Orchestrate multi-step workflows

When a request has multiple stages (the typical pattern is **gather → process →
act**), do this:

1. **Plan.** State a short numbered plan back to the user before executing
   (e.g. "1) read docs A,B,C  2) summarize  3) draft email to X + create a Feishu
   task"). For non-trivial plans, get a quick OK.
2. **Gather.** Read every needed input first (doc reads via `lark-doc`,
   `mail.py read`, etc.). Run independent reads in parallel. Collect results before
   moving on.
3. **Process.** Summarize / extract / decide. Keep a compact working summary you can
   feed into the action steps.
4. **Act.** Execute the outputs. Independent actions (e.g. create a task AND a
   calendar event) can be issued together. Carry forward ids returned by earlier
   steps (e.g. calendar id, task guid) into dependent calls.
5. **Report.** Summarize what was done with concrete handles (message id of the
   email/draft, event id, task link, chat message id).

**Example.** "把这三个飞书文档总结一下，发邮件给老板，并在飞书建个跟进任务":
gather = read 3 docs via `lark-doc`; process = write summary; act =
`mail.py send --to <boss> --subject … --body <summary> --draft` (local-email)
**and** a follow-up task via `lark-task`; report both handles.

## Safety rules (apply across both backends)

- **Confirm before any outward / destructive action:** sending or replying to email,
  posting an IM message, creating/patching calendar events or tasks, deleting/moving
  mail, sharing a doc. Show recipients/title/body/time first and get an explicit OK.
- Respect `lark-cli` risk tiers: never pass `--yes` to a `high-risk-write` without an
  explicit user confirmation.
- When send-intent is unclear, prefer **drafts** (`mail.py … --draft`) and tell the
  user it's ready to review.
- Don't expose tokens, `user_access_token`, OAuth codes, or app secrets in output.
- Read before you write: never assume a doc's content — fetch it.
