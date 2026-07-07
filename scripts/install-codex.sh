#!/usr/bin/env bash
# Install (or uninstall) the ican-assistant Codex adapter (issue #10):
#   1. skills/{office-router,local-email}  -> ~/.agents/skills/    (symlink; --copy to copy)
#   2. adapters/codex/prompts/*.md         -> ~/.codex/prompts/    (/office, /email)
#   3. adapters/codex/AGENTS.md            -> managed block inside ~/.codex/AGENTS.md
#
# Usage:
#   scripts/install-codex.sh [--copy] [--uninstall]
#
# Env overrides (mainly for tests):
#   ICAN_AGENTS_SKILLS_DIR  skills destination  (default: $HOME/.agents/skills)
#   CODEX_HOME              codex config home   (default: $HOME/.codex)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_SRC="$REPO_ROOT/skills"
ADAPTER_DIR="$REPO_ROOT/adapters/codex"
SKILLS=(office-router local-email)
PROMPTS=(office.md email.md)

SKILLS_DEST="${ICAN_AGENTS_SKILLS_DIR:-$HOME/.agents/skills}"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
PROMPTS_DEST="$CODEX_HOME/prompts"
AGENTS_FILE="$CODEX_HOME/AGENTS.md"

BEGIN_MARK='<!-- BEGIN ican-assistant'
END_MARK='<!-- END ican-assistant -->'

MODE=install
COPY=0
for arg in "$@"; do
  case "$arg" in
    --uninstall) MODE=uninstall ;;
    --copy) COPY=1 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg (see --help)" >&2; exit 2 ;;
  esac
done

# Confirm the source really is an ican-assistant skill before rm -rf'ing anything.
is_our_skill_dir() { # $1 = dir, $2 = expected skill name
  [ -f "$1/SKILL.md" ] && grep -q "^name: $2\$" "$1/SKILL.md"
}

strip_managed_block() { # $1 = file; prints content without the managed block
  awk -v b="$BEGIN_MARK" -v e="$END_MARK" '
    index($0, b) == 1 { skip = 1 }
    !skip { print }
    skip && index($0, e) == 1 { skip = 0 }
  ' "$1"
}

install_skills() {
  mkdir -p "$SKILLS_DEST"
  for s in "${SKILLS[@]}"; do
    src="$SKILLS_SRC/$s" dest="$SKILLS_DEST/$s"
    if [ -L "$dest" ]; then
      [ "$COPY" -eq 1 ] && rm "$dest"
    elif [ -e "$dest" ]; then
      if is_our_skill_dir "$dest" "$s"; then
        rm -rf "$dest"
      else
        echo "SKIP $dest: exists and doesn't look like the $s skill — remove it manually" >&2
        continue
      fi
    fi
    if [ "$COPY" -eq 1 ]; then
      cp -R "$src" "$dest"
      echo "copied   $dest"
    else
      ln -sfn "$src" "$dest"
      echo "linked   $dest -> $src"
    fi
  done
}

install_prompts() {
  mkdir -p "$PROMPTS_DEST"
  for p in "${PROMPTS[@]}"; do
    src="$ADAPTER_DIR/prompts/$p" dest="$PROMPTS_DEST/$p"
    if [ -f "$dest" ] && ! cmp -s "$src" "$dest"; then
      cp "$dest" "$dest.bak"
      echo "backup   $dest -> $dest.bak"
    fi
    cp "$src" "$dest"
    echo "prompt   $dest  (/${p%.md})"
  done
}

install_agents_md() {
  mkdir -p "$CODEX_HOME"
  touch "$AGENTS_FILE"
  { strip_managed_block "$AGENTS_FILE"; cat "$ADAPTER_DIR/AGENTS.md"; } > "$AGENTS_FILE.tmp"
  mv "$AGENTS_FILE.tmp" "$AGENTS_FILE"
  echo "agents   managed block updated in $AGENTS_FILE"
}

uninstall() {
  for s in "${SKILLS[@]}"; do
    dest="$SKILLS_DEST/$s"
    if [ -L "$dest" ]; then
      rm "$dest" && echo "removed  $dest (symlink)"
    elif [ -d "$dest" ] && is_our_skill_dir "$dest" "$s"; then
      rm -rf "$dest" && echo "removed  $dest (copy)"
    fi
  done
  for p in "${PROMPTS[@]}"; do
    dest="$PROMPTS_DEST/$p"
    if [ -f "$dest" ] && cmp -s "$ADAPTER_DIR/prompts/$p" "$dest"; then
      rm "$dest" && echo "removed  $dest"
    elif [ -f "$dest" ]; then
      echo "SKIP $dest: modified locally — remove it manually" >&2
    fi
  done
  if [ -f "$AGENTS_FILE" ]; then
    strip_managed_block "$AGENTS_FILE" > "$AGENTS_FILE.tmp"
    mv "$AGENTS_FILE.tmp" "$AGENTS_FILE"
    echo "removed  managed block from $AGENTS_FILE"
  fi
}

if [ "$MODE" = uninstall ]; then
  uninstall
  exit 0
fi

install_skills
install_prompts
install_agents_md

cat <<EOF

Done. Verify inside Codex (CLI or IDE):
  /skills            -> office-router & local-email listed
  \$office-router     -> explicit mention works
  /office, /email    -> custom prompts (also /prompts:office)
Prereqs: python3 + Mail.app automation approval (email), lark-cli auth login (Feishu).
Uninstall: scripts/install-codex.sh --uninstall
EOF
