#!/usr/bin/env bash
# coord-check-hash.sh - Verify file hash for CAS protocol
# Part of Multi-Session Coordination System (Phase 1)
#
# Usage: coord-check-hash.sh <file_path> [expected_hash]
#        coord-check-hash.sh --capture <file_path>
#
# Modes:
#   Default:   Compare current hash against expected, exit 0 if match
#   --capture: Output current hash (for pre-edit capture)
#
# Exit codes:
#   0 - Hash matches (or capture mode)
#   1 - Hash mismatch (conflict detected)
#   2 - File not found
#   3 - Invalid arguments

set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# Argument parsing
# ─────────────────────────────────────────────────────────────────────────────

CAPTURE_MODE=false

if [[ "${1:-}" == "--capture" ]]; then
  CAPTURE_MODE=true
  shift
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: coord-check-hash.sh [--capture] <file_path> [expected_hash]" >&2
  echo "" >&2
  echo "Options:" >&2
  echo "  --capture    Output current hash instead of comparing" >&2
  echo "" >&2
  echo "Examples:" >&2
  echo "  coord-check-hash.sh --capture src/auth.py" >&2
  echo "  coord-check-hash.sh src/auth.py sha256:abc123..." >&2
  exit 3
fi

FILE_PATH="${1}"
EXPECTED_HASH="${2:-}"

# ─────────────────────────────────────────────────────────────────────────────
# Validate file exists
# ─────────────────────────────────────────────────────────────────────────────

if [[ ! -f "$FILE_PATH" ]]; then
  if [[ "$CAPTURE_MODE" == true ]]; then
    # For new files, return a sentinel hash
    echo "sha256:NEW_FILE"
    exit 0
  else
    echo "Error: File not found: $FILE_PATH" >&2
    exit 2
  fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# Calculate current hash
# ─────────────────────────────────────────────────────────────────────────────

# Use shasum (macOS) or sha256sum (Linux)
if command -v shasum &>/dev/null; then
  CURRENT_HASH="sha256:$(shasum -a 256 "$FILE_PATH" | cut -d' ' -f1)"
elif command -v sha256sum &>/dev/null; then
  CURRENT_HASH="sha256:$(sha256sum "$FILE_PATH" | cut -d' ' -f1)"
else
  echo "Error: No SHA256 utility found (need shasum or sha256sum)" >&2
  exit 3
fi

# ─────────────────────────────────────────────────────────────────────────────
# Capture mode: just output the hash
# ─────────────────────────────────────────────────────────────────────────────

if [[ "$CAPTURE_MODE" == true ]]; then
  echo "$CURRENT_HASH"
  exit 0
fi

# ─────────────────────────────────────────────────────────────────────────────
# Compare mode: check against expected
# ─────────────────────────────────────────────────────────────────────────────

if [[ -z "$EXPECTED_HASH" ]]; then
  echo "Error: Expected hash required for comparison mode" >&2
  exit 3
fi

# Normalize expected hash (add prefix if missing)
if [[ ! "$EXPECTED_HASH" =~ ^sha256: ]]; then
  EXPECTED_HASH="sha256:$EXPECTED_HASH"
fi

if [[ "$CURRENT_HASH" == "$EXPECTED_HASH" ]]; then
  echo "MATCH"
  exit 0
else
  echo "CONFLICT"
  echo "  Expected: $EXPECTED_HASH" >&2
  echo "  Current:  $CURRENT_HASH" >&2
  echo "  File:     $FILE_PATH" >&2
  exit 1
fi
