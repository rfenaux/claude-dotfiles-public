#!/bin/bash
# Idempotency Helper for Hooks
#
# Prevents duplicate hook execution using time-based keys.
# Usage: source ~/.claude/hooks/lib/idempotency.sh
#
# Part of: OpenClaw-inspired improvements (Phase 4, F13)
# Created: 2026-01-30

# Configuration
IDEMPOTENCY_LIB="$HOME/.claude/lib"
IDEMPOTENCY_CACHE_DIR="$HOME/.claude/cache/idempotency"

# Ensure cache directory exists
mkdir -p "$IDEMPOTENCY_CACHE_DIR"

# Check if hook should execute (returns 0 if yes, 1 if duplicate)
check_idempotency() {
    local hook_name="$1"
    local context="$2"

    if [[ -z "$hook_name" || -z "$context" ]]; then
        echo "Usage: check_idempotency <hook_name> <context>" >&2
        return 1
    fi

    python3 -c "
import sys
sys.path.insert(0, '$IDEMPOTENCY_LIB')
from idempotency import check_idempotency
result = check_idempotency('$hook_name', '$context')
sys.exit(0 if result else 1)
" 2>/dev/null

    return $?
}

# Clear idempotency for a specific hook/context
clear_idempotency() {
    local hook_name="$1"
    local context="$2"

    python3 -c "
import sys
sys.path.insert(0, '$IDEMPOTENCY_LIB')
from idempotency import clear_idempotency
clear_idempotency('$hook_name', '$context')
" 2>/dev/null
}

# Clear all idempotency cache
clear_all_idempotency() {
    python3 -c "
import sys
sys.path.insert(0, '$IDEMPOTENCY_LIB')
from idempotency import clear_idempotency
clear_idempotency()
" 2>/dev/null
}

# Get idempotency stats
idempotency_stats() {
    python3 -c "
import sys
sys.path.insert(0, '$IDEMPOTENCY_LIB')
from idempotency import get_cache
cache = get_cache()
stats = cache.get_stats()
print(f'Entries: {stats[\"entries\"]}')
print(f'Max: {stats[\"max_entries\"]}')
print(f'TTL: {stats[\"ttl_seconds\"]}s')
" 2>/dev/null
}

# Example usage in hooks:
#
#   #!/bin/bash
#   source ~/.claude/hooks/lib/idempotency.sh
#
#   HOOK_NAME="my-hook"
#   CONTEXT="$FILE_PATH"  # or any unique context
#
#   if ! check_idempotency "$HOOK_NAME" "$CONTEXT"; then
#       exit 0  # Skip - already executed
#   fi
#
#   # ... hook logic here ...
