# PRD: Claude Code 2.1.x Feature Adoption

**Version:** 1.0
**Date:** 2026-01-29
**Author:** Claude Code (Meta-Analysis Follow-up)
**Status:** Draft → Implementation

---

## 1. Problem Statement

### Background

Following the meta-analysis of 703 conversation files, additional optimization opportunities were identified based on Claude Code 2.1.x features that are available but not yet utilized in our configuration.

### Current State Analysis

| Feature | Available Since | Currently Using | Gap |
|---------|----------------|-----------------|-----|
| Wildcard permissions | 2.1.0 | ❌ No | 15+ individual rules could be 5 |
| `once: true` hooks | 2.1.0 | ❌ No | Enhance mode runs every prompt |
| `additionalContext` return | 2.1.0 | ❌ No | RAG cascade not automated |
| `context: fork` | 2.1.0 | ✅ Yes (codex-delegate) | Already implemented |
| Setup hook | 2.1.0 | ❌ No | No auto-setup on --init |
| Skill frontmatter hooks | 2.1.0 | ❌ No | No skill-level validation |
| MCP Search threshold | 2.1.x | ❌ No | Not configured |
| Keybindings | 2.1.x | ❌ No | No keybindings.json exists |

### Key Findings Cross-Referenced

1. **RAG underutilization** (from meta-analysis): 0-2 RAG searches per session vs target 5-10
   - Solution: `additionalContext` hook to auto-inject RAG results

2. **Permission prompts** (friction): Frequent permission requests for common commands
   - Solution: Wildcard permissions `Bash(git *)`, `Bash(npm *)`

3. **Enhance mode overhead**: Runs on every prompt, even approvals
   - Solution: `once: true` or conditional execution

4. **No project auto-setup**: Manual `claude --init` doesn't trigger custom setup
   - Solution: Setup hook for consistent project initialization

---

## 2. Goals & Success Metrics

### Primary Goals

1. Reduce RAG underutilization by auto-injecting context
2. Reduce permission prompts by 80%
3. Reduce per-message overhead from enhance mode
4. Standardize project initialization
5. Enable keyboard shortcuts for frequent actions

### Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| RAG queries/session | 0-2 | 5-10 | Auto-inject on questions |
| Permission prompts/session | 10-15 | 2-3 | Count prompts |
| Enhance hook executions | Every message | First only | Check hook behavior |
| Project setup consistency | Manual | Automated | Setup hook fires |

---

## 3. Solution Design

### 3.1 RAG Cascade Hook (P0)

**Purpose:** Auto-inject RAG results into context for "how/why/what" questions.

**Implementation:**
- Hook type: PreToolUse (on Read tool, catches question context)
- Returns: `additionalContext` with RAG search results
- Trigger: Question patterns detected in tool input

**Hook Script:** `~/.claude/hooks/rag-cascade-inject.sh`

```bash
#!/bin/bash
# Reads tool input, detects question patterns, queries RAG, returns additionalContext
```

**Settings.json Addition:**
```json
{
  "matcher": "Read",
  "hooks": [{
    "type": "command",
    "command": "~/.claude/hooks/rag-cascade-inject.sh"
  }]
}
```

---

### 3.2 Wildcard Permissions (P0)

**Purpose:** Reduce permission prompts by consolidating rules.

**Current State (15+ rules):**
```json
"allow": [
  "Bash(docker --version:*)",
  "Bash(brew list:*)",
  "Bash(brew install:*)",
  "Bash(pip3 show:*)",
  "Bash(mkdir:*)",
  "Bash(curl:*)",
  "Bash(mdfind:*)",
  "Bash(cat:*)",
  "Bash(find:*)",
  ...
]
```

**Proposed State (5 rules):**
```json
"allow": [
  "Bash(git *)",
  "Bash(npm *)",
  "Bash(brew *)",
  "Bash(docker *)",
  "Bash(python *)",
  "Bash(pip *)",
  "Bash(mkdir *)",
  "Bash(curl *)",
  "Bash(stat *)",
  "Bash(ls *)",
  "Bash(wc *)",
  "Bash(head *)",
  "Bash(tail *)",
  "Bash(chmod *)",
  "Bash(cat *)",
  "Bash(find *)",
  "Bash(mdfind *)",
  "Bash(xargs *)",
  "Bash(jq *)",
  "Bash(sed *)",
  "Bash(awk *)",
  "Bash(ollama *)",
  "Bash(codex *)",
  "Bash(gemini *)",
  "Bash(gh *)",
  "Bash(claude *)"
]
```

---

### 3.3 Once-True for Enhance Hook (P0)

**Purpose:** Reduce per-message overhead.

**Current:** Enhance mode message injected on EVERY user prompt.

**Proposed:** Use conditional logic or `once: true` for first prompt only.

**Implementation Options:**

Option A: Use session marker file (more flexible)
```bash
#!/bin/bash
# Only echo if not already shown this session
MARKER="/tmp/claude-enhance-shown-$$"
if [ ! -f "$MARKER" ]; then
    touch "$MARKER"
    echo "[ENHANCE_MODE: ON...]"
fi
```

Option B: Since `once: true` applies per hook instance, keep current approach but optimize the conditional.

**Decision:** Option A - Session marker allows more control.

---

### 3.4 Setup Hook (P1)

**Purpose:** Auto-configure projects on `claude --init` or `--maintenance`.

**Implementation:**
```json
"Setup": [{
  "matcher": "",
  "hooks": [{
    "type": "command",
    "command": "~/.claude/hooks/setup-auto-configure.sh"
  }]
}]
```

**Script Behavior:**
1. Check for existing project configuration
2. Initialize RAG if not present
3. Create `.claude/context/` structure
4. Copy templates if needed
5. Report what was set up

---

### 3.5 Skill Frontmatter Hooks (P1)

**Purpose:** Add validation to potentially dangerous skills.

**Target Skills:**
- `codex-delegate` - Validate OpenAI auth before execution
- `brand-extract` - Validate URL/file exists
- `init-project` - Check not overwriting existing config

**Implementation:** Add hooks to skill frontmatter:
```yaml
---
name: skill-name
hooks:
  PreToolUse:
    - type: command
      command: ~/.claude/hooks/skill-validate-{skill}.sh
---
```

---

### 3.6 MCP Search Threshold (P1)

**Purpose:** Auto-enable MCP tool search when context usage is low.

**Implementation:**
```json
{
  "MCPSearch": "auto:10"
}
```

This enables MCP tool search when context usage is below 10%.

---

### 3.7 Context Fork for codex-delegate (P2)

**Status:** ✅ ALREADY IMPLEMENTED

Verified in `~/.claude/agents/codex-delegate.md`:
```yaml
context: fork
```

No action needed.

---

### 3.8 Custom Keybindings (P2)

**Purpose:** Quick access to frequent actions.

**Implementation:** Create `~/.claude/keybindings.json`:
```json
{
  "checkpoint": {
    "key": "ctrl+shift+c",
    "description": "Create session checkpoint"
  },
  "ctm-status": {
    "key": "ctrl+shift+t",
    "description": "Show CTM task status"
  },
  "rag-status": {
    "key": "ctrl+shift+r",
    "description": "Show RAG index status"
  }
}
```

---

## 4. Implementation Plan

### Phase 1: P0 Quick Wins

| # | Task | Priority | Effort | Dependencies |
|---|------|----------|--------|--------------|
| 1 | Create RAG cascade hook script | P0 | Medium | None |
| 2 | Add RAG cascade hook to settings.json | P0 | Low | Task 1 |
| 3 | Update permissions with wildcards | P0 | Low | None |
| 4 | Optimize enhance hook with session marker | P0 | Low | None |

### Phase 2: P1 Medium Impact

| # | Task | Priority | Effort | Dependencies |
|---|------|----------|--------|--------------|
| 5 | Create setup-auto-configure.sh script | P1 | Medium | None |
| 6 | Add Setup hook to settings.json | P1 | Low | Task 5 |
| 7 | Add frontmatter hooks to key skills | P1 | Medium | None |
| 8 | Add MCPSearch threshold to settings | P1 | Low | None |

### Phase 3: P2 Nice to Have

| # | Task | Priority | Effort | Dependencies |
|---|------|----------|--------|--------------|
| 9 | Create keybindings.json | P2 | Low | None |
| 10 | Verify codex-delegate context:fork | P2 | None | Already done |

---

## 5. Rollback Plan

| Component | Rollback Method |
|-----------|-----------------|
| Hooks | Remove from settings.json, delete script |
| Permissions | Restore from git: `cd ~/.claude && git checkout HEAD~1 settings.json` |
| Keybindings | Delete `~/.claude/keybindings.json` |
| Skill frontmatter | Remove hooks section from skill YAML |

---

## 6. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| RAG hook slows response | Medium | Medium | Cache results, timeout |
| Wildcard too permissive | Low | Medium | Audit allowed commands |
| Setup hook overwrites | Low | High | Check before creating |
| Hook conflicts | Low | Low | Test each hook isolated |

---

## 7. Dependencies

| Dependency | Status |
|------------|--------|
| Claude Code 2.1.x | ✅ v2.1.23 installed |
| RAG system | ✅ Available |
| jq (for hook scripts) | ✅ Installed |
| Settings.json write access | ✅ Available |

---

## 8. Appendix

### A. Reference: additionalContext Hook Return Format

```bash
# Hook script must output JSON to return additionalContext
echo '{"additionalContext": "Injected content here"}'
```

### B. Reference: Wildcard Permission Syntax

- `Bash(git *)` - All git subcommands
- `Bash(* install)` - All commands ending in install
- `Bash(npm run *)` - npm run with any script name

### C. Files to Modify

| File | Action |
|------|--------|
| `~/.claude/settings.json` | Add hooks, update permissions, add MCPSearch |
| `~/.claude/hooks/rag-cascade-inject.sh` | Create |
| `~/.claude/hooks/setup-auto-configure.sh` | Create |
| `~/.claude/hooks/enhance-once.sh` | Create (replace inline) |
| `~/.claude/keybindings.json` | Create |
| `~/.claude/skills/*/SKILL.md` | Add frontmatter hooks |

---

**PRD Status:** Ready for Implementation
**Approval:** Pending user "proceed"
