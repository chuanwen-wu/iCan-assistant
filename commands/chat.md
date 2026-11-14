---
description: Read iCan personal and group conversations in the signed-in browser
---

Use `office-router` to route chat reads to `ican-web`, which opens
`https://icanplatform.feishu.cn/next/messenger/` to read the user's iCan chats.

User request: $ARGUMENTS

1. If the request is empty, list up to ten visible recent personal/group
   conversations, including unread badges or previews when displayed.
2. For a named person or group, locate the matching conversation, verify the
   header, then read messages in the requested time range. Report the visible
   scope and any loading/history limits; do not claim all history was fetched.
3. If login or browser access is unavailable, report the blocker. Do not replace
   browser reads with `lark-im` API results.
4. For requests to send/reply or manage a group, route through `office-router` to
   `lark-im`; confirm the recipient and content before sending. For chat,
   `ican-web` reads conversation messages without posting.
