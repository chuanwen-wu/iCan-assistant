---
description: Read, draft, send, reply to, and manage email through iCan web
---

Use `office-router` to classify this email request. By default, use `ican-web`
for reading, searching, drafting, sending/replying/forwarding, and mailbox actions at
`https://icanplatform.feishu.cn/mail` in the user's signed-in browser.

User request: $ARGUMENTS

Steps:
1. If the request is empty, open the inbox and summarize up to ten visible recent
   messages and the unread count if displayed. State the visible scope.
2. Follow `ican-web` for normal email operations, including replies/forwards in
   the original web thread. If login or browser access is unavailable, report the
   blocker; do not fall back to Apple Mail or `lark-mail`.
3. Prepare the web composer and verify recipients, subject, body and attachments
   before asking for confirmation to send. Confirm the exact targets before
   deleting/moving. If send intent is unclear, keep a web draft and verify its
   save status. If a send outcome is uncertain, inspect the result before doing
   anything else; do not click Send again or resend through another backend.
4. Use `local-email` only when the user explicitly requests Apple Mail; follow
   that skill's CLI and Message-ID requirements.
