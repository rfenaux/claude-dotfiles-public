---
name: config-audit
description: Audit Claude Code configuration - validates imports, checks settings, generates capability manifests. Use /audit for health checks.
argument-hint: [full|quick|imports|manifest]
context: fork
agent: Explore
async:
  mode: never
  require_sync:
    - audit results display
    - user review
---

# Config Audit - Configuration Health Check

Comprehensive audit of Claude Code configuration including memory files, import chains, settings validation, and capability surfacing.

## Trigger

Invoke this skill when:
- User says "/audit", "audit config", "check configuration"
- User asks "what can Claude do?" or "list capabilities"
- User asks "is my config valid?" or "validate setup"
- User mentions "broken imports" or "config issues"
- User wants to generate a capability manifest

## Commands

```bash
# Full audit (all checks)
/audit                  Run full configuration audit
/audit full             Same as above

# Quick audit (fast checks only)
/audit quick            Skip stale reference scan, quick validation

# Specific checks
/audit imports          Only validate @import chains
/audit manifest         Generate CAPABILITIES.md

# Help
/audit help             Show this help
```

## What Gets Checked

### Full Audit
1. **Memory Files** - CLAUDE.md existence, length, location
2. **Import Chains** - Resolves @imports, detects cycles (max 5 hops)
3. **Settings** - JSON validity, hooks configuration
4. **Agents** - Count verification against inventory.json
5. **Skills** - Frontmatter validation, description check
6. **MCP Servers** - Configuration and context impact
7. **Stale References** - Finds outdated file:line refs
8. **Anti-Patterns** - Detects common issues

### Quick Audit
Skips stale reference scan and anti-pattern detection for faster execution.

## Output

### Audit Report
Shows health score (0-100) with:
- **Critical Issues** (score -10 each) - Must fix
- **Warnings** (score -3 each) - Should address
- **Info** - Suggestions and notes
- **Passed** - Checks that succeeded

### Capability Manifest
Generates `~/.claude/CAPABILITIES.md` with:
- All native tools
- MCP tools by server
- Agents by model and auto-invoke status
- Skills with descriptions
- Active hooks by event

## Scripts Called

| Command | Script |
|---------|--------|
| `/audit`, `/audit full` | `~/.claude/scripts/audit-config-chain.sh` |
| `/audit quick` | `~/.claude/scripts/audit-config-chain.sh --quick` |
| `/audit imports` | `~/.claude/scripts/validate-imports.sh` |
| `/audit manifest` | `~/.claude/scripts/generate-capability-manifest.sh` |

## Example Usage

```
User: /audit
Claude: Running full configuration audit...

═══════════════════════════════════════════════════════════════
  Claude Code Configuration Audit
═══════════════════════════════════════════════════════════════

▶ Memory Files
  ✓ User CLAUDE.md length OK (285 lines)
  ✓ Project CLAUDE.md found (45 lines)

▶ Import Chain Validation
  ✓ All imports resolve correctly

▶ Settings Files
  ✓ User settings.json is valid JSON
  ℹ Hooks configured: 5 event types

▶ Agents
  ✓ Agent count matches inventory: 99

▶ Skills
  ℹ Skills found: 7

═══════════════════════════════════════════════════════════════
  Audit Results
═══════════════════════════════════════════════════════════════

Health Score: 94/100 ✓

Critical: 0 | Warnings: 2 | Info: 5 | Passed: 8
```

## Related

- **Agent:** `context-audit-expert` - For deeper analysis and recommendations
- **Script:** `validate-setup.sh` - General setup validation
- **File:** `inventory.json` - Configuration inventory

## Implementation

When user invokes `/audit [mode]`:

1. Parse the mode argument ($ARGUMENTS)
2. Call appropriate script based on mode
3. Display formatted results
4. If issues found, offer recommendations

**For `/audit manifest`:** Generate and confirm location of CAPABILITIES.md
