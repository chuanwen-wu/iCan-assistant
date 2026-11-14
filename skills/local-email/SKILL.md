---
name: local-email
description: 仅在用户明确指定本机 macOS Apple Mail／本地邮件时，使用 scripts/mail.py 读取、发送、回复、草拟和整理邮件。普通 iCan 邮件读取与发送均使用 ican-web 网页技能，不因网页不可用或发送状态不明而回退到本技能。保留原 CLI 兼容能力；lark-mail 停用。
---

# Local Email (Apple Mail control)

Drive the user's Apple Mail through a single CLI wrapper around AppleScript. macOS
only; Mail.app must exist and the terminal must have Automation access to "Mail".

Ordinary iCan email requests, including inbox/search/read, drafting, sending,
replying, forwarding and mailbox changes, use `ican-web` at
`https://icanplatform.feishu.cn/mail`. Use this skill only when the user explicitly
requests Apple Mail. Do not fall back here when the browser is unavailable or a
web send has an uncertain result; resending could create a duplicate. The original
CLI remains available for explicit local use; `lark-mail` / `lark-cli mail` remain
disabled.

**Engine:** `scripts/mail.py`, bundled inside this skill directory (run with
`python3`). Resolve it relative to this SKILL.md — i.e.
`<this-skill-dir>/scripts/mail.py` — wherever the skill is installed.

## How to work

1. Don't read `~/Library/Mail` directly — macOS blocks it (Operation not
   permitted). Always go through `mail.py`, which uses Apple Events.
   **Run it unsandboxed**: command sandboxes (e.g. Codex seatbelt) block Apple
   Events/XPC, which surfaces as a misleading osascript "syntax error" (-2741)
   plus "Connection invalid" XPC noise. If you see that, the script is fine —
   re-run with escalated permissions / outside the sandbox.
2. Messages are addressed by their **message id** (the RFC `Message-ID`), shown in
   `list`/`search` output. Pass it as the first positional arg to
   `read`/`reply`/`mark`/`move`/`delete`.
   A web mailbox row number, subject, URL or accessibility index is not this ID.
   Only if the user explicitly asks to handle a web original in Apple Mail, match the
   account/mailbox, sender, subject and time, then read back and verify a unique
   original before replying or mutating. If it is not synced or ambiguous, stop
   that action instead of choosing an approximate match.
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
