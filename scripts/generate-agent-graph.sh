#!/bin/bash
# Generate agent dependency graph from agent files
# Usage: ./generate-agent-graph.sh [--html]

AGENTS_DIR="$HOME/.claude/agents"
OUTPUT_MD="$HOME/.claude/docs/AGENT_GRAPH.md"
OUTPUT_HTML="$HOME/.claude/docs/agent-graph.html"

# Count agents
AGENT_COUNT=$(ls -1 "$AGENTS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')

# Count by model
OPUS_COUNT=$(grep -l "model: opus" "$AGENTS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
SONNET_COUNT=$(grep -l "model: sonnet" "$AGENTS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
HAIKU_COUNT=$(grep -l "model: haiku" "$AGENTS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')

# Count by async mode
ALWAYS_COUNT=$(grep -l "mode: always" "$AGENTS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
NEVER_COUNT=$(grep -l "mode: never" "$AGENTS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
AUTO_COUNT=$(grep -l "mode: auto" "$AGENTS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')

echo "Agent Statistics:"
echo "  Total: $AGENT_COUNT"
echo "  By Model: opus=$OPUS_COUNT, sonnet=$SONNET_COUNT, haiku=$HAIKU_COUNT"
echo "  By Async: always=$ALWAYS_COUNT, never=$NEVER_COUNT, auto=$AUTO_COUNT"

# Generate HTML visualization if requested
if [[ "$1" == "--html" ]]; then
    cat > "$OUTPUT_HTML" << 'HTMLEOF'
<!DOCTYPE html>
<html>
<head>
    <title>Agent Dependency Graph</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0f0f23;
            color: #fff;
            padding: 20px;
        }
        h1 { text-align: center; margin-bottom: 30px; color: #667eea; }
        .stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 40px;
        }
        .stat-box {
            background: #1a1a3e;
            border-radius: 12px;
            padding: 20px 30px;
            text-align: center;
            border: 1px solid #2a2a5e;
        }
        .stat-number { font-size: 2.5rem; font-weight: bold; color: #06d6a0; }
        .stat-label { color: #8888aa; font-size: 0.9rem; margin-top: 5px; }
        .graph-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        .agent-group {
            background: #1a1a3e;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #2a2a5e;
        }
        .group-title {
            color: #667eea;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #2a2a5e;
        }
        .agent-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #1f1f3f;
        }
        .agent-item:last-child { border-bottom: none; }
        .agent-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        .dot-opus { background: #764ba2; }
        .dot-sonnet { background: #667eea; }
        .dot-haiku { background: #06d6a0; }
        .agent-name { font-size: 0.85rem; }
        .orchestrator { font-weight: bold; color: #fbbf24; }
        .legend {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 30px;
            padding: 15px;
            background: #1a1a3e;
            border-radius: 8px;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.85rem;
            color: #8888aa;
        }
    </style>
</head>
<body>
    <h1>Claude Code Agent Ecosystem</h1>

    <div class="stats">
        <div class="stat-box">
            <div class="stat-number">77</div>
            <div class="stat-label">Total Agents</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">3</div>
            <div class="stat-label">Model Tiers</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">15</div>
            <div class="stat-label">HubSpot Specialists</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">5</div>
            <div class="stat-label">Orchestrators</div>
        </div>
    </div>

    <div class="graph-container">
        <div class="agent-group">
            <div class="group-title">Orchestrators</div>
            <div class="agent-item">
                <div class="agent-dot dot-sonnet"></div>
                <span class="agent-name orchestrator">hubspot-implementation-runbook</span>
            </div>
            <div class="agent-item">
                <div class="agent-dot dot-sonnet"></div>
                <span class="agent-name orchestrator">brand-kit-extractor</span>
            </div>
            <div class="agent-item">
                <div class="agent-dot dot-sonnet"></div>
                <span class="agent-name orchestrator">proposal-orchestrator</span>
            </div>
            <div class="agent-item">
                <div class="agent-dot dot-opus"></div>
                <span class="agent-name orchestrator">reasoning-duo</span>
            </div>
        </div>

        <div class="agent-group">
            <div class="group-title">HubSpot Implementation</div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">hubspot-impl-discovery</span></div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">hubspot-impl-marketing-hub</span></div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">hubspot-impl-sales-hub</span></div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">hubspot-impl-service-hub</span></div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">hubspot-impl-operations-hub</span></div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">hubspot-impl-content-hub</span></div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">hubspot-impl-commerce-hub</span></div>
        </div>

        <div class="agent-group">
            <div class="group-title">Documentation</div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">solution-spec-writer</span></div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">fsd-generator</span></div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">erd-generator</span></div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">bpmn-specialist</span></div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">lucidchart-generator</span></div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">slide-deck-creator</span></div>
        </div>

        <div class="agent-group">
            <div class="group-title">Analysis</div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">roi-calculator</span></div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">risk-analyst-cognita</span></div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">technology-auditor</span></div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">80-20-recommender</span></div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">mvp-scoper</span></div>
        </div>

        <div class="agent-group">
            <div class="group-title">Token Optimization</div>
            <div class="agent-item"><div class="agent-dot dot-haiku"></div><span class="agent-name">codex-delegate</span></div>
            <div class="agent-item"><div class="agent-dot dot-haiku"></div><span class="agent-name">gemini-delegate</span></div>
            <div class="agent-item"><div class="agent-dot dot-haiku"></div><span class="agent-name">worker</span></div>
            <div class="agent-item"><div class="agent-dot dot-haiku"></div><span class="agent-name">meeting-indexer</span></div>
        </div>

        <div class="agent-group">
            <div class="group-title">Brand & Visual</div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">brand-extract-web</span></div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">brand-extract-docs</span></div>
            <div class="agent-item"><div class="agent-dot dot-sonnet"></div><span class="agent-name">brand-kit-compiler</span></div>
        </div>
    </div>

    <div class="legend">
        <div class="legend-item">
            <div class="agent-dot dot-opus"></div>
            <span>Opus (complex)</span>
        </div>
        <div class="legend-item">
            <div class="agent-dot dot-sonnet"></div>
            <span>Sonnet (standard)</span>
        </div>
        <div class="legend-item">
            <div class="agent-dot dot-haiku"></div>
            <span>Haiku (fast)</span>
        </div>
        <div class="legend-item" style="color: #fbbf24;">
            <span>Bold = Orchestrator</span>
        </div>
    </div>
</body>
</html>
HTMLEOF
    echo "HTML visualization generated: $OUTPUT_HTML"
fi

echo ""
echo "Graph documentation: $OUTPUT_MD"
