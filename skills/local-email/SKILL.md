---
name: local-email
description: Read and control the user's local macOS Apple Mail (Mail.app) — list accounts and mailboxes, list/search/read messages, count unread, send, reply, mark read/unread, move, and delete. This is the ONLY mail backend on this Mac — every email intent routes here, including 飞书邮箱 / Feishu Mail (lark-mail is disabled) and the send-email step of any multi-step workflow (e.g. 整理会议纪要后发邮件给参会人). Use whenever the user asks about "my email", "my inbox", "本地邮件", "Apple Mail", 发邮件/发送邮件/写邮件/回复邮件/转发邮件, reading/searching/sending mail on this Mac, or replying to a message. macOS only.
---

# Local Email (Apple Mail control)

Drive the user's Apple Mail through a single CLI wrapper around AppleScript. macOS
only; Mail.app must exist and the terminal must have Automation access to "Mail".

**Engine:** `${CLAUDE_PLUGIN_ROOT}/scripts/mail.py` (run with `python3`).
When this plugin is used in-repo rather than installed, the path is
`plugins/iCan-assistant/scripts/mail.py`.

## How to work

1. Don't read `~/Library/Mail` directly — macOS blocks it (Operation not
   permitted). Always go through `mail.py`, which uses Apple Events.
2. Messages are addressed by their **message id** (the RFC `Message-ID`), shown in
   `list`/`search` output. Pass it as the first positional arg to
   `read`/`reply`/`mark`/`move`/`delete`.
3. Read/mark/move/delete default to the **unified inbox**. If a message lives in
   another mailbox/account, pass `--account` and `--mailbox` matching what `list`
   reported (e.g. `--account iCloud --mailbox Sent\ Messages`).
4. Add `--json` to `accounts/mailboxes/list/search/read/unread-count` when you need
   to parse output programmatically.

## Commands

```
python3 <mail.py> accounts                       # accounts + addresses + enabled state
python3 <mail.py> mailboxes [--account NAME]
python3 <mail.py> list [--limit 20] [--unread] [--account N] [--mailbox M]
python3 <mail.py> search "QUERY" [--limit 20] [--account N] [--mailbox M]
python3 <mail.py> read "<message-id>" [--max-chars 20000] [--account N] [--mailbox M]
python3 <mail.py> unread-count [--account NAME]
python3 <mail.py> send --to a@x.com,b@y.com --subject "S" --body "B" [--cc ...] [--bcc ...] [--from me@x.com] [--draft]
python3 <mail.py> reply "<message-id>" --body "B" [--all] [--from me@x.com] [--draft]
python3 <mail.py> mark "<message-id>" --read | --unread [--account N] [--mailbox M]
python3 <mail.py> move "<message-id>" --to-mailbox Archive [--to-account N] [--account N] [--mailbox M]
python3 <mail.py> delete "<message-id>" [--account N] [--mailbox M]   # moves to Trash
```

## Safety rules (important)

- **Confirm before sending or deleting.** Before `send` / `reply` (without
  `--draft`), show the user the recipients, subject, and body and get an explicit
  OK. Before `delete` / `move`, confirm which message. The user has opted into full
  capability, but these are outward-facing / destructive — never fire them silently.
- When unsure whether the user wants to actually send, use `--draft` first and tell
  them a draft is ready to review in Mail.
- `delete` moves the message to Trash (recoverable), it does not erase permanently.
- Don't surface full message bodies of obviously sensitive mail (banking, OTPs)
  unless the user asked for that specific message.

## Notes

- `search` matches subject/sender substrings within one mailbox (fast, server-side
  filtering via AppleScript `whose`). For full-text body search, read candidates and
  grep their bodies.
- `reply` composes a fresh message to the original sender (or all, with `--all`),
  prefixes the subject with `Re:`, and quotes the original body. Use `--draft` to
  review before it goes out.
- `--from` selects which account sends; it must be one of the addresses shown by
  `accounts`.
