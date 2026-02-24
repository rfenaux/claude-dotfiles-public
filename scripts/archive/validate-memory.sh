#!/usr/bin/env bash
# Validate memory files across all projects
set -euo pipefail
echo "Validating memory files..."
found=0
for mem in ~/.claude/projects/*/memory/MEMORY.md; do
  if [ -f "$mem" ]; then
    lines=$(wc -l < "$mem")
    if [ "$lines" -gt 200 ]; then
      echo "  WARNING: $mem exceeds 200 lines ($lines)"
    fi
    found=$((found + 1))
  fi
done
echo "  $found project memory files validated"
