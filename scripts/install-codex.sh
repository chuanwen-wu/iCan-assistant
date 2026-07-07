#!/usr/bin/env bash
# Install (or uninstall) the ican-assistant Codex adapter (issues #10, #25):
#   1. skills/{office-router,local-email}  -> ~/.agents/skills/   (symlink; --copy to copy)
#      ($HOME-based Agent Skills standard dir — deliberately NOT under CODEX_HOME;
#       both the Codex CLI and the desktop app discover skills there)
#   2. adapters/codex/prompts/*.md         -> <codex home>/prompts/   (/office, /email)
#   3. adapters/codex/AGENTS.md            -> managed block inside <codex home>/AGENTS.md
#
# Codex home detection (#25): the CLI reads $CODEX_HOME from the environment, but the
# desktop app is a GUI process that never sources shell profiles and always uses
# ~/.codex — so prompts/AGENTS.md are installed into EVERY detected home:
#   $CODEX_HOME (env) + CODEX_HOME= found in shell profiles + a live-looking ~/.codex.
#
# Usage:
#   scripts/install-codex.sh [--copy] [--uninstall]
#
# Env overrides (mainly for tests):
#   ICAN_AGENTS_SKILLS_DIR  skills destination (default: $HOME/.agents/skills)
#   ICAN_CODEX_HOMES        colon-separated codex homes; skips detection entirely
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_SRC="$REPO_ROOT/skills"
ADAPTER_DIR="$REPO_ROOT/adapters/codex"
SKILLS=(office-router local-email)
PROMPTS=(office.md email.md)

SKILLS_DEST="${ICAN_AGENTS_SKILLS_DIR:-$HOME/.agents/skills}"

BEGIN_MARK='<!-- BEGIN ican-assistant'
END_MARK='<!-- END ican-assistant -->'

MODE=install
COPY=0
for arg in "$@"; do
  case "$arg" in
    --uninstall) MODE=uninstall ;;
    --copy) COPY=1 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg (see --help)" >&2; exit 2 ;;
  esac
done

# ---- codex home detection (#25) --------------------------------------------

# Last CODEX_HOME= assignment found in the usual shell profiles, with quotes
# stripped and ~ / $HOME expanded. Empty output when none is found.
profile_codex_home() {
  local f line val
  for f in "$HOME/.zshenv" "$HOME/.zprofile" "$HOME/.zshrc" \
           "$HOME/.bash_profile" "$HOME/.bashrc" "$HOME/.profile"; do
    [ -f "$f" ] || continue
    line=$(grep -E '^[[:space:]]*(export[[:space:]]+)?CODEX_HOME=' "$f" | tail -1) || true
    [ -n "$line" ] || continue
    val=${line#*CODEX_HOME=}
    val=${val%%#*}
    val=$(printf '%s' "$val" | sed -e "s/^[[:space:]]*//" -e "s/[[:space:]]*\$//" \
                                   -e "s/^[\"']//" -e "s/[\"']\$//")
    val=${val/#\~/$HOME}
    val=${val//\$\{HOME\}/$HOME}
    val=${val//\$HOME/$HOME}
    if [ -n "$val" ]; then printf '%s\n' "$val"; return 0; fi
  done
  return 0
}

CODEX_HOMES=()
add_codex_home() {
  local h
  [ -n "$1" ] || return 0
  for h in ${CODEX_HOMES[@]+"${CODEX_HOMES[@]}"}; do
    [ "$h" = "$1" ] && return 0
  done
  CODEX_HOMES+=("$1")
}

if [ -n "${ICAN_CODEX_HOMES:-}" ]; then
  IFS=':' read -r -a _homes <<< "$ICAN_CODEX_HOMES"
  for h in "${_homes[@]}"; do add_codex_home "$h"; done
else
  add_codex_home "${CODEX_HOME:-}"
  add_codex_home "$(profile_codex_home)"
  # The GUI desktop app always uses ~/.codex; include it when it looks live.
  if [ -e "$HOME/.codex/config.toml" ] || [ -e "$HOME/.codex/auth.json" ] \
     || [ -e "$HOME/.codex/version.json" ]; then
    add_codex_home "$HOME/.codex"
  fi
  [ "${#CODEX_HOMES[@]}" -gt 0 ] || add_codex_home "$HOME/.codex"
fi

# ---- helpers ----------------------------------------------------------------

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

# ---- install / uninstall ----------------------------------------------------

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

install_prompts() { # $1 = codex home
  mkdir -p "$1/prompts"
  for p in "${PROMPTS[@]}"; do
    src="$ADAPTER_DIR/prompts/$p" dest="$1/prompts/$p"
    if [ -f "$dest" ] && ! cmp -s "$src" "$dest"; then
      cp "$dest" "$dest.bak"
      echo "backup   $dest -> $dest.bak"
    fi
    cp "$src" "$dest"
    echo "prompt   $dest  (/${p%.md})"
  done
}

install_agents_md() { # $1 = codex home
  local agents_file="$1/AGENTS.md"
  mkdir -p "$1"
  touch "$agents_file"
  { strip_managed_block "$agents_file"; cat "$ADAPTER_DIR/AGENTS.md"; } > "$agents_file.tmp"
  mv "$agents_file.tmp" "$agents_file"
  echo "agents   managed block updated in $agents_file"
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
  for home in "${CODEX_HOMES[@]}"; do
    for p in "${PROMPTS[@]}"; do
      dest="$home/prompts/$p"
      if [ -f "$dest" ] && cmp -s "$ADAPTER_DIR/prompts/$p" "$dest"; then
        rm "$dest" && echo "removed  $dest"
      elif [ -f "$dest" ]; then
        echo "SKIP $dest: modified locally — remove it manually" >&2
      fi
    done
    if [ -f "$home/AGENTS.md" ]; then
      strip_managed_block "$home/AGENTS.md" > "$home/AGENTS.md.tmp"
      mv "$home/AGENTS.md.tmp" "$home/AGENTS.md"
      echo "removed  managed block from $home/AGENTS.md"
    fi
  done
}

if [ "$MODE" = uninstall ]; then
  uninstall
  exit 0
fi

install_skills
echo "codex homes: ${CODEX_HOMES[*]}"
for home in "${CODEX_HOMES[@]}"; do
  install_prompts "$home"
  install_agents_md "$home"
done

cat <<EOF

Done. Verify inside Codex (CLI or IDE):
  /skills            -> office-router & local-email listed
  \$office-router     -> explicit mention works
  /office, /email    -> custom prompts (also /prompts:office)
Prereqs: python3 + Mail.app automation approval (email), lark-cli auth login (Feishu).
Uninstall: scripts/install-codex.sh --uninstall
EOF
