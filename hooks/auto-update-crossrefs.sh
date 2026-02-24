#!/bin/bash
# auto-update-crossrefs.sh - FULLY AUTOMATED agent/skill cross-reference maintenance
# PostToolUse hook for Write/Edit to agents/ or skills/
# Auto-detects clusters, auto-updates siblings, auto-generates descriptions

# Circuit breaker: skip if too many recent failures
. "$HOME/.claude/hooks/lib/circuit-breaker.sh" 2>/dev/null
check_circuit "auto-update-crossrefs" || exit 0

set +e  # fail-silent: hooks must not abort on error

AGENTS_DIR="$HOME/.claude/agents"
SKILLS_DIR="$HOME/.claude/skills"
CLUSTERS_FILE="$HOME/.claude/config/agent-clusters.json"

# Read tool input from stdin
input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // ""')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // .tool_input.path // ""')

# Only process Write/Edit to agents/ or skills/
case "$tool_name" in
    Write|Edit) ;;
    *) exit 0 ;;
esac

case "$file_path" in
    */.claude/agents/*.md) type="agent"; dir="$AGENTS_DIR" ;;
    */.claude/skills/*.md|*/.claude/skills/*/SKILL.md) type="skill"; dir="$SKILLS_DIR" ;;
    *) exit 0 ;;
esac

# Extract name from path
if [ "$type" = "agent" ]; then
    name=$(basename "$file_path" .md)
else
    if [[ "$file_path" == */SKILL.md ]]; then
        name=$(basename "$(dirname "$file_path")")
    else
        name=$(basename "$file_path" .md)
    fi
fi

# Check if file exists (create/modify) or was deleted
file_exists=false
[ -f "$file_path" ] && file_exists=true

# Initialize clusters file if needed
init_clusters() {
    [ -f "$CLUSTERS_FILE" ] && return
    mkdir -p "$(dirname "$CLUSTERS_FILE")"
    cat > "$CLUSTERS_FILE" << 'EOF'
{
  "clusters": {
    "hubspot-impl": {
      "orchestrator": "hubspot-implementation-runbook",
      "pattern": "^hubspot-impl-",
      "members": []
    },
    "specs": {
      "pattern": "(spec-|fsd-|brief-)",
      "members": []
    },
    "diagrams": {
      "pattern": "(erd-|bpmn-|lucidchart-|architecture-|mermaid-)",
      "members": []
    },
    "presentations": {
      "pattern": "(slide-|deck-|presentation-|pitch-)",
      "members": []
    },
    "commercial": {
      "pattern": "(roi-|commercial-|80-20-|options-)",
      "members": []
    },
    "reasoning": {
      "pattern": "^reasoning-",
      "members": []
    },
    "discovery": {
      "pattern": "(discovery-|questionnaire-)",
      "members": []
    },
    "memory": {
      "pattern": "(ctm-|memory-|rag-.*expert|claude-md-)",
      "members": []
    },
    "brand": {
      "orchestrator": "brand-kit-extractor",
      "pattern": "^brand-",
      "members": []
    },
    "delegation": {
      "pattern": "(-delegate$|^worker$)",
      "members": []
    }
  }
}
EOF
}

# Auto-detect cluster from agent name using patterns
detect_cluster() {
    local agent_name="$1"
    init_clusters

    # Loop through clusters and test patterns
    for cluster_name in $(jq -r '.clusters | keys[]' "$CLUSTERS_FILE" 2>/dev/null); do
        local pattern=$(jq -r --arg c "$cluster_name" '.clusters[$c].pattern // ""' "$CLUSTERS_FILE" 2>/dev/null)
        if [ -n "$pattern" ]; then
            if echo "$agent_name" | grep -qE "$pattern" 2>/dev/null; then
                echo "$cluster_name"
                return 0
            fi
        fi
    done
    echo ""
}

# Get agent description from frontmatter
get_agent_description() {
    local agent_file="$1"
    sed -n '/^---$/,/^---$/p' "$agent_file" 2>/dev/null | grep "^description:" | sed 's/^description: *//' | head -1
}

# Generate short "when to use" from description
generate_when_to_use() {
    local description="$1"
    # Extract key differentiator (first phrase or key words)
    echo "$description" | sed 's/\..*//' | cut -c1-50 | sed 's/$/.../' 2>/dev/null || echo "Alternative option"
}

# Get cluster members
get_cluster_members() {
    local cluster="$1"
    jq -r --arg cluster "$cluster" '.clusters[$cluster].members[]' "$CLUSTERS_FILE" 2>/dev/null
}

# Get cluster orchestrator
get_cluster_orchestrator() {
    local cluster="$1"
    jq -r --arg cluster "$cluster" '.clusters[$cluster].orchestrator // ""' "$CLUSTERS_FILE" 2>/dev/null
}

# Add agent to cluster in JSON
add_to_cluster_json() {
    local cluster="$1"
    local agent_name="$2"

    # Check if already in cluster
    if jq -e --arg cluster "$cluster" --arg name "$agent_name" \
        '.clusters[$cluster].members | index($name)' "$CLUSTERS_FILE" >/dev/null 2>&1; then
        return 0
    fi

    # Add to cluster
    jq --arg cluster "$cluster" --arg name "$agent_name" \
        '.clusters[$cluster].members += [$name]' "$CLUSTERS_FILE" > "${CLUSTERS_FILE}.tmp" \
        && mv "${CLUSTERS_FILE}.tmp" "$CLUSTERS_FILE"
}

# Remove agent from cluster in JSON
remove_from_cluster_json() {
    local cluster="$1"
    local agent_name="$2"

    jq --arg cluster "$cluster" --arg name "$agent_name" \
        '.clusters[$cluster].members -= [$name]' "$CLUSTERS_FILE" > "${CLUSTERS_FILE}.tmp" \
        && mv "${CLUSTERS_FILE}.tmp" "$CLUSTERS_FILE"
}

# Add Related Agents section if missing
ensure_related_agents_section() {
    local agent_file="$1"

    if ! grep -q "## Related Agents" "$agent_file" 2>/dev/null; then
        # Add section at end of file
        cat >> "$agent_file" << 'EOF'

---

## Related Agents

| Agent | When to Use Instead |
|-------|---------------------|
EOF
    fi
}

# Add agent to another agent's Related Agents table
add_to_related_agents() {
    local target_file="$1"
    local new_agent="$2"
    local when_to_use="$3"

    # Skip if agent already in table
    if grep -q "| \`$new_agent\`" "$target_file" 2>/dev/null; then
        return 0
    fi

    # Ensure section exists
    ensure_related_agents_section "$target_file"

    # Add row after the header separator line
    sed -i '' "/^|-------|---------------------|$/a\\
| \`$new_agent\` | $when_to_use |
" "$target_file" 2>/dev/null || true
}

# Remove agent from Related Agents table
remove_from_related_agents() {
    local target_file="$1"
    local agent_to_remove="$2"

    [ -f "$target_file" ] && sed -i '' "/| \`$agent_to_remove\` |/d" "$target_file" 2>/dev/null || true
}

# Add to orchestrator's delegates_to
add_to_delegates() {
    local orchestrator_file="$1"
    local new_agent="$2"

    [ ! -f "$orchestrator_file" ] && return 0

    # Check if delegates_to exists
    if ! grep -q "^delegates_to:" "$orchestrator_file" 2>/dev/null; then
        # Add delegates_to after description in frontmatter
        sed -i '' '/^description:/a\
delegates_to:\
  - '"$new_agent"'
' "$orchestrator_file" 2>/dev/null || true
        return 0
    fi

    # Check if already listed
    if grep -q "^  - $new_agent$" "$orchestrator_file" 2>/dev/null; then
        return 0
    fi

    # Add to existing delegates_to
    sed -i '' "/^delegates_to:$/a\\
\  - $new_agent" "$orchestrator_file" 2>/dev/null || true
}

# Remove from orchestrator's delegates_to
remove_from_delegates() {
    local orchestrator_file="$1"
    local agent_to_remove="$2"

    [ -f "$orchestrator_file" ] && sed -i '' "/^  - $agent_to_remove$/d" "$orchestrator_file" 2>/dev/null || true
}

# Main logic for agents
if [ "$type" = "agent" ]; then
    init_clusters

    # Detect cluster
    cluster=$(detect_cluster "$name")

    if [ "$file_exists" = "true" ]; then
        # Agent created or modified

        if [ -n "$cluster" ]; then
            # Add to cluster JSON
            add_to_cluster_json "$cluster" "$name"

            # Get orchestrator
            orchestrator=$(get_cluster_orchestrator "$cluster")

            # Add to orchestrator's delegates_to (if not the orchestrator itself)
            if [ -n "$orchestrator" ] && [ "$name" != "$orchestrator" ]; then
                add_to_delegates "$AGENTS_DIR/${orchestrator}.md" "$name"
            fi

            # Get description for "when to use"
            description=$(get_agent_description "$file_path")
            when_to_use=$(generate_when_to_use "$description")

            # Add to all sibling agents' Related Agents
            for member in $(get_cluster_members "$cluster"); do
                if [ "$member" != "$name" ] && [ -f "$AGENTS_DIR/${member}.md" ]; then
                    add_to_related_agents "$AGENTS_DIR/${member}.md" "$name" "$when_to_use"
                fi
            done

            # Add siblings to this agent's Related Agents
            ensure_related_agents_section "$file_path"
            for member in $(get_cluster_members "$cluster"); do
                if [ "$member" != "$name" ] && [ -f "$AGENTS_DIR/${member}.md" ]; then
                    member_desc=$(get_agent_description "$AGENTS_DIR/${member}.md")
                    member_when=$(generate_when_to_use "$member_desc")
                    add_to_related_agents "$file_path" "$member" "$member_when"
                fi
            done

            echo "[X-Ref] Auto-updated '$name' in cluster '$cluster'"
        else
            echo "[X-Ref] Agent '$name' - no cluster pattern matched"
        fi
    else
        # Agent deleted - find which cluster it was in
        for c in $(jq -r '.clusters | keys[]' "$CLUSTERS_FILE" 2>/dev/null); do
            if jq -e --arg c "$c" --arg name "$name" '.clusters[$c].members | index($name)' "$CLUSTERS_FILE" >/dev/null 2>&1; then
                cluster="$c"
                break
            fi
        done

        if [ -n "$cluster" ]; then
            # Remove from cluster JSON
            remove_from_cluster_json "$cluster" "$name"

            # Remove from orchestrator's delegates_to
            orchestrator=$(get_cluster_orchestrator "$cluster")
            if [ -n "$orchestrator" ]; then
                remove_from_delegates "$AGENTS_DIR/${orchestrator}.md" "$name"
            fi

            # Remove from all sibling agents' Related Agents
            for member in $(get_cluster_members "$cluster"); do
                remove_from_related_agents "$AGENTS_DIR/${member}.md" "$name"
            done

            echo "[X-Ref] Removed '$name' from cluster '$cluster'"
        fi

        # Also scan ALL agents to remove any stale references
        for agent_file in "$AGENTS_DIR"/*.md; do
            remove_from_related_agents "$agent_file" "$name"
            sed -i '' "/^  - $name$/d" "$agent_file" 2>/dev/null || true
        done
    fi
fi

exit 0
