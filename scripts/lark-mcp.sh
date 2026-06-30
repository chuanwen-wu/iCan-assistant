#!/usr/bin/env bash
# Self-contained launcher for the official Feishu/Lark MCP server
# (@larksuiteoapi/lark-mcp). Bundled with the iCan-assistant plugin so the
# whole plugin folder is copyable.
#
# Credentials are read from environment variables; if FEISHU_APP_ID is not
# already set, we source the first .env we find, in this order:
#   1. $FEISHU_ENV_FILE                (explicit override)
#   2. $CLAUDE_PLUGIN_ROOT/.env        (plugin-local, gitignored)
#   3. <this script>/../.env           (plugin-local when run directly)
#   4. $PWD/.env                       (host project)
# Secrets never live in committed config — only in a .env you create.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

load_env() {
  local f="$1"
  [ -n "$f" ] && [ -f "$f" ] || return 1
  set -a; . "$f"; set +a
  return 0
}

if [ -z "${FEISHU_APP_ID:-}" ]; then
  load_env "${FEISHU_ENV_FILE:-}" \
    || load_env "${CLAUDE_PLUGIN_ROOT:-}/.env" \
    || load_env "$here/../.env" \
    || load_env "$PWD/.env" \
    || true
fi

: "${FEISHU_APP_ID:?FEISHU_APP_ID missing (set it in the environment or a .env file)}"
: "${FEISHU_APP_SECRET:?FEISHU_APP_SECRET missing (set it in the environment or a .env file)}"

# Tool presets: IM (chat/message), calendar, docs, and tasks — the four office
# surfaces this plugin routes to. Override with FEISHU_MCP_TOOLS if needed.
TOOLS="${FEISHU_MCP_TOOLS:-preset.im.default,preset.calendar.default,preset.doc.default,preset.task.default}"

exec npx -y @larksuiteoapi/lark-mcp mcp \
  --app-id "$FEISHU_APP_ID" \
  --app-secret "$FEISHU_APP_SECRET" \
  --language "${FEISHU_MCP_LANG:-zh}" \
  --token-mode auto \
  --oauth \
  --tools "$TOOLS"
