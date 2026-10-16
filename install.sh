#!/usr/bin/env bash
set -euo pipefail

REPOSITORY="ChosenOneDevv/VCPS"
REF="main"
ADAPTER=""
TARGET="${PWD}"
TARGET_EXPLICIT=0
GLOBAL_INSTALL=0
TUI=0
FORWARD_ARGS=()

usage() {
  cat <<'EOF'
Install VCPS directly from GitHub.

Usage:
  install.sh                         # animated interactive installer
  install.sh --adapter codex [--target PATH] [--global] [installer options]
  install.sh --adapter claude-code [--target PATH] [--global] [installer options]
  install.sh --tui [--target PATH]
  install.sh --help

Options:
  --adapter NAME  Required: codex or claude-code
  --target PATH   Project repository (defaults to current directory)
  --global        User-wide install (Codex ~/.agents, Claude Code ~/.claude)
  --tui           Open animated interactive installer
  --ref REF       GitHub branch or tag (defaults to main)
  --plan          Preview changes without writing
  --verify        Verify an existing install
EOF
}

while (($#)); do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --adapter)
      (($# >= 2)) || { echo "missing value for --adapter" >&2; exit 2; }
      ADAPTER="$2"; FORWARD_ARGS+=(--adapter "$2"); shift 2 ;;
    --target)
      (($# >= 2)) || { echo "missing value for --target" >&2; exit 2; }
      TARGET="$2"; TARGET_EXPLICIT=1; FORWARD_ARGS+=(--target "$2"); shift 2 ;;
    --global)
      GLOBAL_INSTALL=1; FORWARD_ARGS+=(--global); shift ;;
    --tui) TUI=1; shift ;;
    --ref)
      (($# >= 2)) || { echo "missing value for --ref" >&2; exit 2; }
      REF="$2"; shift 2 ;;
    *) FORWARD_ARGS+=("$1"); shift ;;
  esac
done

if [[ -z "$ADAPTER" && -t 1 && -r /dev/tty ]]; then TUI=1; fi
if [[ "$TUI" == 1 && -n "$ADAPTER" ]]; then
  echo "--tui cannot be combined with --adapter" >&2; exit 2
fi
if [[ "$TUI" == 0 ]]; then
[[ "$ADAPTER" == "codex" || "$ADAPTER" == "claude-code" ]] || {
  echo "choose --adapter codex or --adapter claude-code" >&2; exit 2;
}
fi
[[ "$GLOBAL_INSTALL" == 0 || "$TARGET_EXPLICIT" == 0 ]] || {
  echo "--global cannot be combined with --target" >&2; exit 2;
}
case "$REF" in
  ""|-*|*..*|*[!a-zA-Z0-9._/-]*)
    echo "invalid GitHub ref: $REF" >&2; exit 2 ;;
esac

command -v curl >/dev/null || { echo "curl is required" >&2; exit 2; }
command -v tar >/dev/null || { echo "tar is required" >&2; exit 2; }
command -v python3 >/dev/null || { echo "Python 3 is required" >&2; exit 2; }

TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

ARCHIVE_URL="https://codeload.github.com/${REPOSITORY}/tar.gz/${REF}"
echo "Downloading VCPS ${REPOSITORY}@${REF}..."
curl --proto '=https' --tlsv1.2 --fail --location --retry 2 "$ARCHIVE_URL" \
  --output "$TMP_DIR/vcps.tar.gz"
mkdir "$TMP_DIR/source"
tar -xzf "$TMP_DIR/vcps.tar.gz" --strip-components=1 -C "$TMP_DIR/source"

if [[ "$TUI" == 1 ]]; then
  python3 "$TMP_DIR/source/adapters/installer_tui.py" \
    --source "$TMP_DIR/source" --target "$TARGET"
  exit $?
fi

if [[ "$GLOBAL_INSTALL" == 0 && "$TARGET_EXPLICIT" == 0 ]]; then
  FORWARD_ARGS+=(--target "$TARGET")
fi
python3 "$TMP_DIR/source/adapters/install.py" "${FORWARD_ARGS[@]}"
