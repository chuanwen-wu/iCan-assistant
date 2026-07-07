---
description: Office copilot — route email/Feishu requests and orchestrate multi-step workflows
argument-hint: [request]
---

Use the `office-router` skill to handle this request. It coordinates local Apple
Mail (the `local-email` skill's engine — `scripts/mail.py` inside that skill's
directory, run with `python3`) and Feishu/Lark (`lark-cli` + the `lark-*` skills).
Feishu actions run as the user's own identity (`lark-cli config default-as user`;
one-time `lark-cli auth login` required).

Request: $ARGUMENTS

Steps:
1. Classify the request into email and/or Feishu intents (docs, calendar, tasks, IM,
   多维表格, 电子表格, 妙记, …).
2. If it's a multi-step workflow, state a short numbered plan first (gather →
   process → act) **with each step tagged with its backend/skill**, then execute.
3. Route each intent to the right backend per the office-router skill. Email steps
   always go to `local-email` (`mail.py`) — never `lark-mail` / `lark-cli mail` —
   even when every other step of the workflow runs in Feishu (妙记/文档/日历).
4. Confirm before any outward/destructive action (send/reply email, post IM, create
   or patch calendar events/tasks, delete/move mail, share doc). Prefer `--draft`
   for email when send intent is unclear.
5. If the request is empty, show a quick status: `mail.py unread-count`,
   `mail.py list --limit 10`, and offer Feishu actions.
