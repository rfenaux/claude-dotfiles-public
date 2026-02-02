#!/usr/bin/env bash
#
# generate-routing-index.sh - Generate routing-index.json from current config
#
# Usage: ~/.claude/scripts/generate-routing-index.sh
#
# This script:
# 1. Reads auto_invoke agents from inventory.json
# 2. Calculates guide file sizes
# 3. Outputs routing-index.json with triggers and metadata
#

set -euo pipefail

CLAUDE_DIR="${HOME}/.claude"
OUTPUT_FILE="${CLAUDE_DIR}/routing-index.json"
INVENTORY_FILE="${CLAUDE_DIR}/inventory.json"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo -e "${GREEN}Generating routing-index.json...${NC}"

# Check dependencies
if ! command -v jq &> /dev/null; then
    echo "Error: jq is required. Install with: brew install jq"
    exit 1
fi

if [[ ! -f "$INVENTORY_FILE" ]]; then
    echo "Error: inventory.json not found. Run generate-inventory.sh first."
    exit 1
fi

# Get auto-invoke agents from inventory
AUTO_INVOKE_AGENTS=$(jq -r '.auto_invoke.agents[]' "$INVENTORY_FILE" 2>/dev/null || echo "")

# Calculate guide sizes
declare -A GUIDE_SIZES
for guide in GARDEN_PROTECTION RAG_GUIDE CTM_GUIDE CDP_PROTOCOL PRD-multi-session-coordination AGENTS_INDEX SKILLS_INDEX ASYNC_ROUTING LESSONS_GUIDE PROJECT_MEMORY_GUIDE BINARY_FILE_REFERENCE HUBSPOT_IMPLEMENTATION_GUIDE RESOURCE_MANAGEMENT CONFIGURATION_GUIDE; do
    file="${CLAUDE_DIR}/${guide}.md"
    if [[ -f "$file" ]]; then
        GUIDE_SIZES[$guide]=$(wc -l < "$file" | tr -d ' ')
    else
        GUIDE_SIZES[$guide]=0
    fi
done

# Categorize by size
categorize_size() {
    local size=$1
    if (( size < 150 )); then
        echo "small"
    elif (( size <= 500 )); then
        echo "medium"
    else
        echo "large"
    fi
}

# Generate JSON
cat > "$OUTPUT_FILE" << 'HEADER'
{
  "version": "1.0",
HEADER

echo "  \"generated\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"," >> "$OUTPUT_FILE"

cat >> "$OUTPUT_FILE" << 'BODY'
  "description": "O(1) lookup index for agent triggers and guide routing",

  "auto_invoke_agents": {
    "erd-generator": {
      "triggers": ["erd", "entity relationship", "data model diagram", "database schema"],
      "model": "sonnet",
      "async": "never"
    },
    "bpmn-specialist": {
      "triggers": ["bpmn", "business process", "process diagram", "swim lane", "workflow diagram"],
      "model": "sonnet",
      "async": "never"
    },
    "lucidchart-generator": {
      "triggers": ["lucidchart", "lucid diagram", "export to lucidchart"],
      "model": "sonnet",
      "async": "never"
    },
    "rag-search-agent": {
      "triggers": ["project question", ".rag/ exists", "what did we decide", "requirements"],
      "model": "sonnet",
      "async": "auto",
      "condition": ".rag/ directory exists in project"
    },
    "brand-kit-extractor": {
      "triggers": ["brand kit", "extract brand", "brand colors", "color scheme", "brand identity"],
      "model": "sonnet",
      "async": "auto"
    },
    "hubspot-implementation-runbook": {
      "triggers": ["hubspot implementation", "implement hubspot", "runbook mode", "set up hubspot"],
      "model": "sonnet",
      "async": "auto"
    },
    "proposal-orchestrator": {
      "triggers": ["create proposal", "proposal package", "full proposal", "proposal bundle"],
      "model": "sonnet",
      "async": "auto"
    },
    "reasoning-duo": {
      "triggers": ["think harder", "debate this", "sanity check", "architecture design", "2+ failures"],
      "model": "sonnet",
      "async": "never",
      "escalates_to": "reasoning-trio"
    },
    "reasoning-duo-cg": {
      "triggers": ["claude and gemini", "research together", "long context", "web-grounded", ">200K context"],
      "model": "sonnet",
      "async": "never"
    },
    "reasoning-trio": {
      "triggers": ["all three models", "full consensus", "critical decision", "production deployment"],
      "model": "sonnet",
      "async": "never",
      "escalated_from": ["reasoning-duo", "reasoning-duo-cg"]
    },
    "codex-delegate": {
      "triggers": ["bulk analysis", "token optimization", "multi-file", "code generation"],
      "model": "haiku",
      "async": "always",
      "fallback": "gemini-delegate"
    },
    "gemini-delegate": {
      "triggers": ["use gemini", "free option", "large context", "codex unavailable"],
      "model": "haiku",
      "async": "always",
      "fallback_for": "codex-delegate"
    }
  },

  "skills": {
    "solution-architect": {
      "triggers": ["architect mode", "sa mode", "act as solution architect", "erd", "bpmn", "integration design"]
    },
    "project-discovery": {
      "triggers": ["discovery session", "gather requirements", "assess project", "validate scope"]
    },
    "hubspot-specialist": {
      "triggers": ["hubspot question", "hub features", "hubspot api", "hubspot tier"]
    },
    "pptx": {
      "triggers": ["create presentation", "powerpoint", "slides", "deck"]
    },
    "doc-coauthoring": {
      "triggers": ["write a doc", "documentation", "proposal draft", "spec draft"]
    },
    "decision-tracker": {
      "triggers": ["record decision", "we decided", "let's go with", "decision made"]
    },
    "brand-extract": {
      "triggers": ["extract brand", "brand kit", "brand colors from"]
    },
    "ctm": {
      "triggers": ["what am I working on", "task status", "switch task", "spawn task"]
    },
    "init-project": {
      "triggers": ["init project", "initialize memory", "set up project"]
    }
  },

  "guides": {
BODY

# Add guide entries with calculated sizes
first=true
for guide in GARDEN_PROTECTION RAG_GUIDE CTM_GUIDE CDP_PROTOCOL PRD-multi-session-coordination AGENTS_INDEX SKILLS_INDEX ASYNC_ROUTING LESSONS_GUIDE PROJECT_MEMORY_GUIDE BINARY_FILE_REFERENCE HUBSPOT_IMPLEMENTATION_GUIDE RESOURCE_MANAGEMENT CONFIGURATION_GUIDE; do
    size=${GUIDE_SIZES[$guide]}
    category=$(categorize_size "$size")

    if [[ "$first" == "true" ]]; then
        first=false
    else
        echo "," >> "$OUTPUT_FILE"
    fi

    echo -n "    \"${guide}.md\": { \"size\": $size, \"category\": \"$category\" }" >> "$OUTPUT_FILE"
done

cat >> "$OUTPUT_FILE" << 'FOOTER'

  },

  "priority_rules": [
    { "need": "ERD for CRM project", "use": "erd-generator", "not": "visual-documentation-skills" },
    { "need": "BPMN with Lucidchart export", "use": "bpmn-specialist", "not": "flowchart-creator" },
    { "need": "ASCII diagram in markdown", "use": "itp:graph-easy", "not": "manual ASCII" },
    { "need": "PDF from markdown", "use": "doc-tools:pandoc-pdf-generation", "not": "raw pandoc" },
    { "need": "HubSpot implementation", "use": "hubspot-implementation-runbook", "not": "hubspot-specialist skill" }
  ]
}
FOOTER

# Count entries
auto_invoke_count=$(jq '.auto_invoke_agents | length' "$OUTPUT_FILE")
skills_count=$(jq '.skills | length' "$OUTPUT_FILE")
guides_count=$(jq '.guides | length' "$OUTPUT_FILE")

echo -e "${GREEN}Generated routing-index.json:${NC}"
echo "  - Auto-invoke agents: $auto_invoke_count"
echo "  - Skills: $skills_count"
echo "  - Guides: $guides_count"
echo ""
echo -e "${YELLOW}Guide sizes:${NC}"
for guide in "${!GUIDE_SIZES[@]}"; do
    size=${GUIDE_SIZES[$guide]}
    category=$(categorize_size "$size")
    printf "  %-40s %4d lines (%s)\n" "${guide}.md" "$size" "$category"
done | sort -t':' -k2 -n
