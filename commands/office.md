---
description: Office copilot — route email/Feishu requests and orchestrate multi-step workflows
---

Use the `office-router` skill to handle this request. It coordinates `ican-web`
(browser email operations and chat reads), `local-email` (explicit Apple Mail
requests only), and Feishu/Lark
(`lark-cli` + the `lark-*` skills for other actions). CLI actions run as the user's
own identity (`lark-cli config default-as user`; one-time `lark-cli auth login`
required); browser operations use the user's signed-in iCan web session.

Request: $ARGUMENTS

Steps:
1. Classify the request into email and/or Feishu intents (docs, calendar, tasks, IM,
   多维表格, 电子表格, 妙记, …).
2. If it's a multi-step workflow, state a short numbered plan first (gather →
   process → act) **with each step tagged with its backend/skill**, then execute.
3. Route normal email operations and personal/group chat reads to `ican-web`,
   including email drafting/sending/replying/forwarding and mailbox changes within
   multi-step workflows. IM writes go to `lark-im`. Use `local-email` only for an
   explicit Apple Mail request; never use `lark-mail` / `lark-cli mail` for email.
4. Confirm before any outward/destructive action (send/reply email, post IM, create
   or patch calendar events/tasks, delete/move mail, share doc). Prepare email in
   the web composer before confirmation; when send intent is unclear, keep a web
   draft and verify its save status. If sending has an uncertain result, inspect
   it without sending again or switching backends.
5. If the request is empty, open the iCan web inbox with `ican-web`, summarize up
   to ten visible recent messages, and offer chat or other Feishu actions.
