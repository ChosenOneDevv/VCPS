#!/usr/bin/env bash
# LIVE_ADAPTER_EXECUTION: drives a real `claude -p` invocation of the
# /vcps-setup skill against a disposable fixture repository.
#
# This is opt-in and NOT run as part of run_tests.py's structural/simulated
# suite. It requires: the `claude` CLI, network access to the API, and a
# fixture repository the invocation is allowed to read/write inside.
#
# Usage:
#   ./run_live.sh <fixture-dir> [-- extra claude args]
#
# The fixture directory MUST be outside the VCPS source tree (see
# evaluation/setup-scenarios.md and the adapter self-audit in
# evaluation/claude-code-adapter.md "Known limitations" for why: this
# script never points at the VCPS repository itself in non-dev-mode runs).
#
# This script only ever passes --dry-run by default, because a live
# mutating run has not yet been exercised for this adapter version
# (see adapters/claude-code/README.md "Known limitations"). Pass
# --allow-mutate explicitly to drop --dry-run; doing so against anything
# other than a disposable fixture is the caller's responsibility, not
# this script's.

set -euo pipefail

ADAPTER_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VCPS_ROOT="$(cd "${ADAPTER_ROOT}/../.." && pwd)"

if [ "${1:-}" = "" ] || [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  echo "Usage: $0 <fixture-dir> [--allow-mutate]"
  echo "  fixture-dir   a disposable repository OUTSIDE ${VCPS_ROOT}"
  echo "  --allow-mutate  drop the default --dry-run (use only on a disposable fixture)"
  exit 1
fi

FIXTURE_DIR="$(cd "$1" && pwd)"
shift || true

case "${FIXTURE_DIR}" in
  "${VCPS_ROOT}"*)
    echo "refusing: fixture directory is inside the VCPS repository (${VCPS_ROOT})" >&2
    echo "live runs must target a disposable fixture outside the VCPS source tree" >&2
    exit 2
    ;;
esac

MODE_ARG="--dry-run"
if [ "${1:-}" = "--allow-mutate" ]; then
  MODE_ARG=""
  shift || true
fi

if ! command -v claude >/dev/null 2>&1; then
  echo '{"error": "claude CLI not found on PATH"}' >&2
  exit 3
fi

SKILL_LINK="${FIXTURE_DIR}/.claude/skills/vcps-setup"
if [ ! -e "${SKILL_LINK}" ]; then
  mkdir -p "${FIXTURE_DIR}/.claude/skills"
  ln -s "${ADAPTER_ROOT}/vcps-setup" "${SKILL_LINK}"
  echo "linked skill into fixture: ${SKILL_LINK} -> ${ADAPTER_ROOT}/vcps-setup"
fi

echo "=== LIVE_ADAPTER_EXECUTION ==="
echo "fixture: ${FIXTURE_DIR}"
echo "core:    ${VCPS_ROOT}"
echo "mode:    /vcps-setup ${MODE_ARG} --core ${VCPS_ROOT}"
echo "==============================="

if ! BEFORE_TREE="$(python3 "${ADAPTER_ROOT}/tests/fingerprint_fixture.py" "${FIXTURE_DIR}")"; then
  echo "failed to fingerprint fixture before Claude invocation" >&2
  exit 4
fi

if (cd "${FIXTURE_DIR}" && claude -p "/vcps-setup ${MODE_ARG} --core ${VCPS_ROOT}" "$@"); then
  STATUS=0
else
  STATUS=$?
fi

if ! AFTER_TREE="$(python3 "${ADAPTER_ROOT}/tests/fingerprint_fixture.py" "${FIXTURE_DIR}")"; then
  echo "failed to fingerprint fixture after Claude invocation" >&2
  exit 4
fi

echo "--- fixture-tree comparison (runs even if the CLI call failed) ---"
if [ "${BEFORE_TREE}" = "${AFTER_TREE}" ]; then
  echo "tree unchanged"
else
  echo "tree CHANGED:"
  diff <(echo "${BEFORE_TREE}") <(echo "${AFTER_TREE}") || true
fi

exit "${STATUS}"
