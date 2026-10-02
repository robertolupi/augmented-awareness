#!/usr/bin/env bash
# Wait for a target file to exist and be non-empty.
#
# Usage:
#   wait-for-file.sh <file-path> [timeout-seconds] [interval-seconds]
#
# Arguments:
#   file-path         Target file to wait for.
#   timeout-seconds   Maximum seconds to wait (default: 120).
#   interval-seconds  Polling interval in seconds (default: 1).
#
# Environment variables:
#   WAIT_NEWER_THAN_SEC   If set, file mtime must be > this epoch timestamp.
#
# Exit codes:
#   0 when the target file exists and is ready
#   1 on timeout
set -euo pipefail

TARGET="${1:-}"
TIMEOUT="${2:-120}"
INTERVAL="${3:-1}"

if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 <file-path> [timeout-seconds] [interval-seconds]" >&2
  exit 1
fi

get_mtime() {
  local f="$1"
  if [[ "$OSTYPE" == "darwin"* ]]; then
    stat -f %m "$f" 2>/dev/null || echo 0
  else
    stat -c %Y "$f" 2>/dev/null || echo 0
  fi
}

start_time=$(date +%s)
echo "Waiting up to ${TIMEOUT}s for: $TARGET" >&2

while true; do
  if [[ -f "$TARGET" && -s "$TARGET" ]]; then
    if [[ -n "${WAIT_NEWER_THAN_SEC:-}" ]]; then
      mtime=$(get_mtime "$TARGET")
      if (( mtime > WAIT_NEWER_THAN_SEC )); then
        echo "Ready: $TARGET (${mtime} > ${WAIT_NEWER_THAN_SEC})" >&2
        exit 0
      fi
    else
      echo "Ready: $TARGET" >&2
      exit 0
    fi
  fi

  now=$(date +%s)
  elapsed=$(( now - start_time ))
  if (( elapsed >= TIMEOUT )); then
    echo "Timed out after ${TIMEOUT}s waiting for $TARGET" >&2
    exit 1
  fi

  sleep "$INTERVAL"
done
