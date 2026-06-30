---
name: office-router
description: Entry point and orchestrator for office tasks on this Mac. Use whenever the user asks anything about email or Feishu/Lark (邮件/收件箱/Apple Mail, 飞书/Lark 文档/云文档/wiki, 日历/会议, 任务/待办/todo, 群/消息/发消息), OR asks for a multi-step office workflow (e.g. read documents then summarize then send an email / create a calendar event / create tasks). This skill classifies the request, routes each part to local Apple Mail or the lark MCP, and orchestrates multi-step plans end to end.
---

# Office Router & Orchestrator

You coordinate two backends to get office work done on this Mac:

| Backend | How to call it | Use for |
|---|---|---|
| **Local Apple Mail** | `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/mail.py …` (see the `local-email` skill) | reading/searching/sending/replying email, inbox triage |
| **Feishu / Lark** | `lark` MCP tools (`mcp__lark__*`) | docs/wiki, calendar, tasks, IM/chat/messages |

If the `lark` MCP tools are not loaded, fetch them with ToolSearch (e.g.
`query: "lark calendar task doc im"`) before using them.

## Step 1 — Classify the request

Split the user request into one or more **intents**. Map keywords/scenarios:

- **Email** (→ local-email): 邮件, 收件箱, 未读, Apple Mail, 发邮件, 回复, 收到的…, an
  `@`-address recipient, "send/reply/forward", checking what someone emailed.
- **Feishu docs** (→ lark): 飞书文档/云文档/docx, wiki/知识库, a `feishu.cn/.../docx/…`
  or `/wiki/…` or `/drive/folder/…` link, "读文档/总结文档".
- **Feishu calendar** (→ lark): 日历, 日程, 会议, 约时间, freebusy, "安排/创建会议".
- **Feishu tasks** (→ lark): 任务, 待办, todo, 清单, "建任务/提醒".
- **Feishu IM** (→ lark): 群, 群聊, 发消息给…, chat, 通知某人.

Default folder for Feishu docs when the user gives no link (project convention):
`https://icanplatform.feishu.cn/drive/folder/RtWofl1yalrpKYd9tS1c8STnnqd`.

If an intent is genuinely ambiguous (e.g. "通知团队" could be email or a Feishu
group), ask one short clarifying question; otherwise pick the obvious backend and
proceed.

## Step 2 — Route (tool map)

**Email** — delegate to the `local-email` skill. Common ones:
`mail.py list --unread`, `mail.py search "…"`, `mail.py read "<id>"`,
`mail.py send --to … --subject … --body …` (use `--draft` when intent to send is
unclear).

**Feishu docs / wiki:**
- Read a doc body: `mcp__lark__docx_v1_document_rawContent`
- Search docs: `mcp__lark__docx_builtin_search`; wiki: `mcp__lark__wiki_v1_node_search`,
  `mcp__lark__wiki_v2_space_getNode`
- Import markdown as a doc: `mcp__lark__docx_builtin_import`
- Share a doc: `mcp__lark__drive_v1_permissionMember_create`

**Feishu calendar:**
- `mcp__lark__calendar_v4_calendar_primary` → get the primary calendar id
- `mcp__lark__calendar_v4_calendarEvent_create` / `_patch` / `_get`
- `mcp__lark__calendar_v4_freebusy_list` to check availability before scheduling

**Feishu tasks:**
- `mcp__lark__task_v2_task_create`, `_patch`, `_addMembers`, `_addReminders`

**Feishu IM:**
- `mcp__lark__im_v1_chat_list` / `_chat_create` / `_chatMembers_get`
- `mcp__lark__im_v1_message_create` (send), `_message_list` (read)

## Step 3 — Orchestrate multi-step workflows

When a request has multiple stages (the typical pattern is **gather → process →
act**), do this:

1. **Plan.** State a short numbered plan back to the user before executing
   (e.g. "1) read docs A,B,C  2) summarize  3) draft email to X + create a Feishu
   task"). For non-trivial plans, get a quick OK.
2. **Gather.** Read every needed input first (multiple `docx_v1_document_rawContent`
   calls, `mail.py read`, etc.). Run independent reads in parallel. Collect results
   before moving on.
3. **Process.** Summarize / extract / decide. Keep a compact working summary you can
   feed into the action steps.
4. **Act.** Execute the outputs. Independent actions (e.g. create a task AND a
   calendar event) can be issued together. Carry forward ids returned by earlier
   steps (e.g. calendar id, task guid) into dependent calls.
5. **Report.** Summarize what was done with concrete handles (message id of the
   email/draft, event id, task link, chat message id).

**Example.** "把这三个飞书文档总结一下，发邮件给老板，并在飞书建个跟进任务":
gather = 3× `docx_v1_document_rawContent`; process = write summary; act =
`mail.py send --to <boss> --subject … --body <summary> --draft` **and**
`task_v2_task_create` with the follow-up; report both handles.

## Safety rules (apply across both backends)

- **Confirm before any outward / destructive action:** sending or replying to email,
  posting an IM message, creating/patching calendar events or tasks, deleting/moving
  mail, sharing a doc. Show recipients/title/body/time first and get an explicit OK.
- When send-intent is unclear, prefer **drafts** (`mail.py … --draft`) and tell the
  user it's ready to review.
- Don't expose `.env` secrets, app tokens, `user_access_token`, or OAuth codes in
  output.
- Read before you write: never assume a doc's content — fetch it.
