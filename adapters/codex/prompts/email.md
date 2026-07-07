---
description: Read or control local Apple Mail (list/search/read/send/reply/mark/move/delete)
argument-hint: [request]
---

Use the `local-email` skill to act on the user's local Apple Mail.

Engine: `scripts/mail.py` inside the `local-email` skill directory (resolve it
relative to that skill's SKILL.md, e.g. `~/.agents/skills/local-email/scripts/mail.py`),
run with `python3`.

User request: $ARGUMENTS

Steps:
1. If the request is empty, show a quick inbox snapshot: run `unread-count` and
   `list --limit 10`, then summarize.
2. Otherwise pick the right subcommand. Always go through `mail.py` — never read
   `~/Library/Mail` directly.
3. For `send`/`reply` (real send) and `delete`/`move`: confirm recipients/subject/
   body or the target message with the user before executing. Prefer `--draft` when
   the user hasn't clearly said "send it".
