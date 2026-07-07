#!/usr/bin/env python3
"""
local-email: control macOS Apple Mail (Mail.app) from the command line via AppleScript.

This is the engine behind the `local-email` Claude Code plugin. It shells out to
`/usr/bin/osascript`, so it only works on macOS with Mail.app, and the controlling
terminal must be granted Automation access to "Mail" (System Settings ->
Privacy & Security -> Automation). No Full Disk Access is required because we never
read ~/Library/Mail directly (macOS blocks that anyway); everything goes through
Apple Events.

Records are returned by AppleScript using control-character delimiters so that
subjects/bodies containing tabs or newlines never corrupt the output:
  - fields within a record separated by US  (unit separator, 0x1F)
  - records separated by RS  (record separator, 0x1E)

Usage examples:
  mail.py accounts
  mail.py mailboxes --account iCloud
  mail.py list --limit 20 --unread
  mail.py list --account iCloud --mailbox INBOX --limit 10
  mail.py search "invoice" --limit 20
  mail.py read "<message-id>"
  mail.py unread-count
  mail.py send --to a@x.com,b@y.com --subject "Hi" --body "Hello" [--cc ...] [--bcc ...] [--from me@x.com] [--draft]
  mail.py reply "<message-id>" --body "Thanks!" [--all] [--draft]
  mail.py mark "<message-id>" --read | --unread
  mail.py move "<message-id>" --to-mailbox Archive [--account iCloud]
  mail.py delete "<message-id>"          # moves the message to Trash

Add --json to any read/list command for machine-readable output.
"""
import argparse
import json
import subprocess
import sys

US = "\x1f"  # unit separator: between fields
RS = "\x1e"  # record separator: between records


def run_osascript(script: str, args=None):
    """Run an AppleScript whose top-level handler is `on run argv`.

    `args` are passed as argv items, so user-supplied strings never need to be
    escaped into AppleScript string literals (avoids injection / quoting bugs).
    """
    args = [str(a) for a in (args or [])]
    proc = subprocess.run(
        ["/usr/bin/osascript", "-", *args],
        input=script,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        err = proc.stderr.strip() or "osascript failed"
        sys.stderr.write(err + "\n")
        if "Not authorized to send Apple events" in err or "-1743" in err:
            sys.stderr.write(
                "\nHint: grant this terminal Automation access to 'Mail' in "
                "System Settings -> Privacy & Security -> Automation.\n"
            )
        elif "-2741" in err or "-600" in err or "connection invalid" in err.lower():
            # The bundled scripts are known-good. Both signatures mean a sandbox
            # blocked Apple Events/XPC to Mail: -2741 is a bogus "syntax error"
            # (Mail's scripting terms couldn't load at compile time); -600
            # "Application isn't running" appears even while Mail is running.
            sys.stderr.write(
                "\nHint: this is NOT a script bug — the process appears to be "
                "sandboxed and blocked from talking to Mail (Apple Events/XPC). "
                "Re-run this command outside the sandbox: in agents that sandbox "
                "shell commands (e.g. Codex), request approval to run with "
                "escalated permissions. (If Mail.app is genuinely not running in "
                "a GUI session, open it first.)\n"
            )
        sys.exit(2)
    return proc.stdout


def box_clause(var="theBox"):
    """AppleScript snippet that resolves `acct`/`mbox` argv values into a mailbox.

    Empty account => unified `inbox`. Otherwise `mailbox mbox of account acct`,
    defaulting the mailbox name to INBOX when blank.
    """
    return f"""
    if acct is "" then
      set {var} to inbox
    else
      if mbox is "" then set mbox to "INBOX"
      set {var} to mailbox mbox of account acct
    end if
"""


def parse_records(out):
    out = out.rstrip(RS + "\n")
    if not out:
        return []
    return [rec.split(US) for rec in out.split(RS)]


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def cmd_accounts(a):
    script = """
on run argv
  set US to (character id 31)
  set RS to (character id 30)
  tell application "Mail"
    set out to ""
    repeat with acc in accounts
      set addrs to ""
      try
        set addrs to (email addresses of acc) as string
      end try
      set stval to "enabled"
      try
        if not (enabled of acc) then set stval to "disabled"
      end try
      set out to out & (name of acc) & US & addrs & US & stval & RS
    end repeat
    return out
  end tell
end run
"""
    recs = parse_records(run_osascript(script))
    rows = [{"name": r[0], "addresses": r[1], "status": r[2]} for r in recs]
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for r in rows:
            print(f"{r['name']:<28} {r['addresses']:<35} [{r['status']}]")


def cmd_mailboxes(a):
    script = """
on run argv
  set acct to item 1 of argv
  set US to (character id 31)
  set RS to (character id 30)
  tell application "Mail"
    set out to ""
    if acct is "" then
      repeat with acc in accounts
        repeat with mb in mailboxes of acc
          set out to out & (name of acc) & US & (name of mb) & RS
        end repeat
      end repeat
    else
      repeat with mb in mailboxes of account acct
        set out to out & acct & US & (name of mb) & RS
      end repeat
    end if
    return out
  end tell
end run
"""
    recs = parse_records(run_osascript(script, [a.account or ""]))
    rows = [{"account": r[0], "mailbox": r[1]} for r in recs]
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for r in rows:
            print(f"{r['account']:<28} {r['mailbox']}")


def cmd_list(a):
    script = f"""
on run argv
  set acct to item 1 of argv
  set mbox to item 2 of argv
  set lim to (item 3 of argv) as integer
  set unreadOnly to (item 4 of argv) is "1"
  set US to (character id 31)
  set RS to (character id 30)
  tell application "Mail"
    {box_clause()}
    if unreadOnly then
      set msgs to (messages of theBox whose read status is false)
    else
      set msgs to messages of theBox
    end if
    set n to count of msgs
    if lim > 0 and lim < n then set n to lim
    set out to ""
    repeat with i from 1 to n
      set m to item i of msgs
      set rdflag to "0"
      if read status of m then set rdflag to "1"
      set ds to ""
      try
        set ds to (date received of m) as string
      end try
      set sndr to ""
      try
        set sndr to (sender of m) as string
      end try
      set out to out & (message id of m) & US & rdflag & US & sndr & US & ds & US & (subject of m) & RS
    end repeat
    return out
  end tell
end run
"""
    recs = parse_records(
        run_osascript(script, [a.account or "", a.mailbox or "", a.limit, "1" if a.unread else "0"])
    )
    rows = [
        {"message_id": r[0], "read": r[1] == "1", "sender": r[2], "date": r[3], "subject": r[4]}
        for r in recs
    ]
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        if not rows:
            print("(no messages)")
        for r in rows:
            flag = " " if r["read"] else "*"
            print(f"{flag} {r['date'][:21]:<21} {r['sender'][:30]:<30} {r['subject']}")
            print(f"    id: {r['message_id']}")


def cmd_search(a):
    script = f"""
on run argv
  set acct to item 1 of argv
  set mbox to item 2 of argv
  set q to item 3 of argv
  set lim to (item 4 of argv) as integer
  set US to (character id 31)
  set RS to (character id 30)
  tell application "Mail"
    {box_clause()}
    set msgs to (messages of theBox whose (subject contains q) or (sender contains q))
    set n to count of msgs
    if lim > 0 and lim < n then set n to lim
    set out to ""
    repeat with i from 1 to n
      set m to item i of msgs
      set rdflag to "0"
      if read status of m then set rdflag to "1"
      set ds to ""
      try
        set ds to (date received of m) as string
      end try
      set sndr to ""
      try
        set sndr to (sender of m) as string
      end try
      set out to out & (message id of m) & US & rdflag & US & sndr & US & ds & US & (subject of m) & RS
    end repeat
    return out
  end tell
end run
"""
    recs = parse_records(
        run_osascript(script, [a.account or "", a.mailbox or "", a.query, a.limit])
    )
    rows = [
        {"message_id": r[0], "read": r[1] == "1", "sender": r[2], "date": r[3], "subject": r[4]}
        for r in recs
    ]
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        if not rows:
            print("(no matches)")
        for r in rows:
            flag = " " if r["read"] else "*"
            print(f"{flag} {r['date'][:21]:<21} {r['sender'][:30]:<30} {r['subject']}")
            print(f"    id: {r['message_id']}")


def cmd_read(a):
    script = f"""
on run argv
  set theId to item 1 of argv
  set acct to item 2 of argv
  set mbox to item 3 of argv
  set maxc to (item 4 of argv) as integer
  set RS to (character id 30)
  tell application "Mail"
    {box_clause()}
    set matches to (messages of theBox whose message id is theId)
    if (count of matches) is 0 then return "ERR_NOT_FOUND"
    set m to item 1 of matches
    set b to ""
    try
      set b to content of m
    end try
    if maxc > 0 and (count of characters of b) > maxc then set b to (text 1 thru maxc of b)
    set ds to ""
    try
      set ds to (date received of m) as string
    end try
    set tos to ""
    try
      set tos to (address of to recipients of m) as string
    end try
    return (subject of m) & RS & (sender of m) & RS & tos & RS & ds & RS & b
  end tell
end run
"""
    out = run_osascript(script, [a.message_id, a.account or "", a.mailbox or "", a.max_chars])
    if out.strip() == "ERR_NOT_FOUND":
        sys.stderr.write("Message not found in the given mailbox (default INBOX). "
                         "Try --account/--mailbox matching the list output.\n")
        sys.exit(3)
    parts = out.rstrip("\n").split(RS)
    while len(parts) < 5:
        parts.append("")
    rec = {"subject": parts[0], "sender": parts[1], "to": parts[2], "date": parts[3], "body": parts[4]}
    if a.json:
        print(json.dumps(rec, ensure_ascii=False, indent=2))
    else:
        print(f"Subject: {rec['subject']}")
        print(f"From:    {rec['sender']}")
        print(f"To:      {rec['to']}")
        print(f"Date:    {rec['date']}")
        print("-" * 60)
        print(rec["body"])


def cmd_unread_count(a):
    script = """
on run argv
  set acct to item 1 of argv
  tell application "Mail"
    if acct is "" then
      return (count of (messages of inbox whose read status is false)) as string
    else
      set c to 0
      try
        set c to count of (messages of (mailbox "INBOX" of account acct) whose read status is false)
      end try
      return c as string
    end if
  end tell
end run
"""
    out = run_osascript(script, [a.account or ""]).strip()
    if a.json:
        print(json.dumps({"account": a.account or "(all inboxes)", "unread": int(out or 0)}))
    else:
        print(f"{out} unread in {a.account or 'unified inbox'}")


def _split_addrs(s):
    return ",".join(p.strip() for p in (s or "").split(",") if p.strip())


def cmd_send(a):
    script = """
on run argv
  set toList to item 1 of argv
  set ccList to item 2 of argv
  set bccList to item 3 of argv
  set subj to item 4 of argv
  set bodyText to item 5 of argv
  set fromAddr to item 6 of argv
  set doSend to (item 7 of argv) is "1"
  tell application "Mail"
    set newMsg to make new outgoing message with properties {subject:subj, content:bodyText, visible:false}
    tell newMsg
      repeat with a in (my splitText(toList))
        make new to recipient at end of to recipients with properties {address:a}
      end repeat
      repeat with a in (my splitText(ccList))
        make new cc recipient at end of cc recipients with properties {address:a}
      end repeat
      repeat with a in (my splitText(bccList))
        make new bcc recipient at end of bcc recipients with properties {address:a}
      end repeat
      if fromAddr is not "" then set sender to fromAddr
    end tell
    if doSend then
      send newMsg
      return "SENT"
    else
      save newMsg
      return "DRAFT_SAVED"
    end if
  end tell
end run

on splitText(s)
  if s is "" then return {}
  set AppleScript's text item delimiters to ","
  set parts to text items of s
  set AppleScript's text item delimiters to ""
  return parts
end splitText
"""
    out = run_osascript(
        script,
        [
            _split_addrs(a.to),
            _split_addrs(a.cc),
            _split_addrs(a.bcc),
            a.subject,
            a.body,
            a.from_addr or "",
            "0" if a.draft else "1",
        ],
    ).strip()
    print({"SENT": "Message sent.", "DRAFT_SAVED": "Draft saved (not sent)."}.get(out, out))


def cmd_reply(a):
    # Fetch the original, then compose a fresh reply deterministically (more
    # reliable than Mail's `reply` verb, which depends on GUI state).
    fetch = f"""
on run argv
  set theId to item 1 of argv
  set acct to item 2 of argv
  set mbox to item 3 of argv
  set RS to (character id 30)
  tell application "Mail"
    {box_clause()}
    set matches to (messages of theBox whose message id is theId)
    if (count of matches) is 0 then return "ERR_NOT_FOUND"
    set m to item 1 of matches
    set tos to ""
    try
      set tos to (address of to recipients of m) as string
    end try
    set ccs to ""
    try
      set ccs to (address of cc recipients of m) as string
    end try
    set b to ""
    try
      set b to content of m
    end try
    return (sender of m) & RS & (subject of m) & RS & tos & RS & ccs & RS & b
  end tell
end run
"""
    out = run_osascript(fetch, [a.message_id, a.account or "", a.mailbox or ""])
    if out.strip() == "ERR_NOT_FOUND":
        sys.stderr.write("Original message not found in the given mailbox.\n")
        sys.exit(3)
    parts = out.rstrip("\n").split(RS)
    while len(parts) < 5:
        parts.append("")
    orig_sender, orig_subject, orig_to, orig_cc, orig_body = parts[:5]

    # Extract a bare address from "Name <addr>" form for the To: field.
    def bare(addr):
        if "<" in addr and ">" in addr:
            return addr[addr.index("<") + 1 : addr.index(">")].strip()
        return addr.strip()

    to_addr = bare(orig_sender)
    cc = ""
    if a.all:
        extra = [x for x in (orig_to + "," + orig_cc).split(",") if x.strip()]
        cc = _split_addrs(",".join(extra))
    subject = orig_subject if orig_subject.lower().startswith("re:") else "Re: " + orig_subject
    quoted = "\n\n----- Original message from {} -----\n{}".format(orig_sender, orig_body)
    body = a.body + quoted

    # Delegate to the send path.
    send_args = argparse.Namespace(
        to=to_addr, cc=cc, bcc="", subject=subject, body=body,
        from_addr=a.from_addr, draft=a.draft,
    )
    cmd_send(send_args)


def cmd_mark(a):
    val = "true" if a.read else "false"
    script = f"""
on run argv
  set theId to item 1 of argv
  set acct to item 2 of argv
  set mbox to item 3 of argv
  tell application "Mail"
    {box_clause()}
    set matches to (messages of theBox whose message id is theId)
    if (count of matches) is 0 then return "ERR_NOT_FOUND"
    set read status of (item 1 of matches) to {val}
    return "OK"
  end tell
end run
"""
    out = run_osascript(script, [a.message_id, a.account or "", a.mailbox or ""]).strip()
    if out == "ERR_NOT_FOUND":
        sys.stderr.write("Message not found.\n")
        sys.exit(3)
    print(f"Marked as {'read' if a.read else 'unread'}.")


def cmd_move(a):
    script = f"""
on run argv
  set theId to item 1 of argv
  set acct to item 2 of argv
  set mbox to item 3 of argv
  set targetBox to item 4 of argv
  set targetAcct to item 5 of argv
  tell application "Mail"
    {box_clause()}
    set matches to (messages of theBox whose message id is theId)
    if (count of matches) is 0 then return "ERR_NOT_FOUND"
    if targetAcct is "" then
      set dest to mailbox targetBox
    else
      set dest to mailbox targetBox of account targetAcct
    end if
    move (item 1 of matches) to dest
    return "OK"
  end tell
end run
"""
    out = run_osascript(
        script,
        [a.message_id, a.account or "", a.mailbox or "", a.to_mailbox, a.to_account or (a.account or "")],
    ).strip()
    if out == "ERR_NOT_FOUND":
        sys.stderr.write("Message not found.\n")
        sys.exit(3)
    print(f"Moved to {a.to_mailbox}.")


def cmd_delete(a):
    script = f"""
on run argv
  set theId to item 1 of argv
  set acct to item 2 of argv
  set mbox to item 3 of argv
  tell application "Mail"
    {box_clause()}
    set matches to (messages of theBox whose message id is theId)
    if (count of matches) is 0 then return "ERR_NOT_FOUND"
    delete (item 1 of matches)
    return "OK"
  end tell
end run
"""
    out = run_osascript(script, [a.message_id, a.account or "", a.mailbox or ""]).strip()
    if out == "ERR_NOT_FOUND":
        sys.stderr.write("Message not found.\n")
        sys.exit(3)
    print("Deleted (moved to Trash).")


def build_parser():
    p = argparse.ArgumentParser(prog="mail.py", description="Control Apple Mail via AppleScript.")
    sub = p.add_subparsers(dest="cmd", required=True)

    # Shared flag, attached to every subparser so `--json` works *after* the
    # subcommand (its natural position, e.g. `mail.py list --json`).
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="machine-readable JSON output")

    sp = sub.add_parser("accounts", parents=[common], help="list Mail accounts")
    sp.set_defaults(func=cmd_accounts)

    sp = sub.add_parser("mailboxes", parents=[common], help="list mailboxes (optionally for one account)")
    sp.add_argument("--account")
    sp.set_defaults(func=cmd_mailboxes)

    sp = sub.add_parser("list", parents=[common], help="list messages in a mailbox (default: unified inbox)")
    sp.add_argument("--account")
    sp.add_argument("--mailbox")
    sp.add_argument("--limit", type=int, default=20)
    sp.add_argument("--unread", action="store_true", help="only unread messages")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("search", parents=[common], help="search subject/sender within a mailbox")
    sp.add_argument("query")
    sp.add_argument("--account")
    sp.add_argument("--mailbox")
    sp.add_argument("--limit", type=int, default=20)
    sp.set_defaults(func=cmd_search)

    sp = sub.add_parser("read", parents=[common], help="read a message body by message id")
    sp.add_argument("message_id")
    sp.add_argument("--account")
    sp.add_argument("--mailbox")
    sp.add_argument("--max-chars", type=int, default=20000, dest="max_chars")
    sp.set_defaults(func=cmd_read)

    sp = sub.add_parser("unread-count", parents=[common], help="count unread in inbox")
    sp.add_argument("--account")
    sp.set_defaults(func=cmd_unread_count)

    sp = sub.add_parser("send", help="compose and send (or save as draft) a message")
    sp.add_argument("--to", required=True, help="comma-separated addresses")
    sp.add_argument("--cc", default="")
    sp.add_argument("--bcc", default="")
    sp.add_argument("--subject", required=True)
    sp.add_argument("--body", required=True)
    sp.add_argument("--from", dest="from_addr", help="sender address (must be one of your accounts)")
    sp.add_argument("--draft", action="store_true", help="save as draft instead of sending")
    sp.set_defaults(func=cmd_send)

    sp = sub.add_parser("reply", help="reply to a message by message id")
    sp.add_argument("message_id")
    sp.add_argument("--body", required=True)
    sp.add_argument("--all", action="store_true", help="reply to all original recipients")
    sp.add_argument("--account")
    sp.add_argument("--mailbox")
    sp.add_argument("--from", dest="from_addr")
    sp.add_argument("--draft", action="store_true")
    sp.set_defaults(func=cmd_reply)

    sp = sub.add_parser("mark", help="mark a message read/unread")
    sp.add_argument("message_id")
    g = sp.add_mutually_exclusive_group(required=True)
    g.add_argument("--read", action="store_true")
    g.add_argument("--unread", dest="read", action="store_false")
    sp.add_argument("--account")
    sp.add_argument("--mailbox")
    sp.set_defaults(func=cmd_mark)

    sp = sub.add_parser("move", help="move a message to another mailbox")
    sp.add_argument("message_id")
    sp.add_argument("--to-mailbox", required=True, dest="to_mailbox")
    sp.add_argument("--to-account", dest="to_account")
    sp.add_argument("--account")
    sp.add_argument("--mailbox")
    sp.set_defaults(func=cmd_move)

    sp = sub.add_parser("delete", help="delete a message (moves it to Trash)")
    sp.add_argument("message_id")
    sp.add_argument("--account")
    sp.add_argument("--mailbox")
    sp.set_defaults(func=cmd_delete)

    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
