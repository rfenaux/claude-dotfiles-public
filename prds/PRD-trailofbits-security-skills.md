# PRD: Trail of Bits Security Skills Integration

> **Status**: Draft | **Author**: Claude | **Date**: 2026-02-04

## 1. Executive Summary

Integrate Trail of Bits security skills into Raphael's Claude Code configuration to enhance security analysis capabilities during code reviews, audits, and vulnerability detection workflows.

## 2. Problem Statement

Current setup lacks:
- Structured security analysis methodology for code reviews
- CodeQL/Semgrep integration patterns
- Systematic vulnerability variant analysis
- Security-focused differential review workflows

## 3. Proposed Solution

Selectively install 8 high-value Trail of Bits skills that complement existing setup without duplication.

### 3.1 Skills to Install (Tier 1 - High Value)

| Skill | Purpose | Integration Point |
|-------|---------|-------------------|
| `differential-review` | Security-focused PR/commit review | `/review-pr` enhancement |
| `static-analysis` (semgrep) | Fast pattern-based security scanning | New `/semgrep` skill |
| `static-analysis` (codeql) | Deep interprocedural analysis | New `/codeql` skill |
| `variant-analysis` | Find similar vulns across codebase | After vuln discovery |
| `sharp-edges` | Identify dangerous API patterns | Code review |
| `audit-context-building` | Deep context before vuln hunting | Audit workflow |
| `fix-review` | Detect bug introductions in fixes | Post-fix verification |

### 3.2 Skills to Skip

| Skill | Reason |
|-------|--------|
| `building-secure-contracts` | No blockchain work |
| `entry-point-analyzer` | Smart contract specific |
| `spec-to-code-compliance` | Blockchain audit specific |
| `yara-authoring` | Malware analysis not needed |
| `firebase-apk-scanner` | Mobile security not needed |
| `modern-python` | Hook conflicts with existing uv workflow |
| `culture-index` | Team culture assessment - irrelevant |
| `burpsuite-project-parser` | No Burp Suite usage |

### 3.3 Skills to Defer (Tier 2)

| Skill | Reason to Defer |
|-------|-----------------|
| `constant-time-analysis` | Crypto-specific, evaluate later |
| `property-based-testing` | Good but not urgent |
| `dwarf-expert` | Binary analysis - niche |
| `insecure-defaults` | Evaluate after Tier 1 |

## 4. Implementation Architecture

### 4.1 Installation Method

**Option A: Plugin Marketplace (Recommended)**
```bash
/plugin marketplace add trailofbits/skills
/plugin install differential-review@trailofbits
/plugin install static-analysis@trailofbits
# ... etc
```

**Option B: Manual Skill Copy**
- Clone repo to temp location
- Copy specific skill folders to `~/.claude/skills/`
- Avoids plugin dependency, more control

**Decision**: Use **Option B** for granular control and security isolation.

### 4.2 Directory Structure

```
~/.claude/skills/security/
├── tob-differential-review/
│   └── SKILL.md (copied from Trail of Bits)
├── tob-semgrep/
│   └── SKILL.md
├── tob-codeql/
│   └── SKILL.md
├── tob-variant-analysis/
│   └── SKILL.md
├── tob-sharp-edges/
│   └── SKILL.md
├── tob-audit-context/
│   └── SKILL.md
└── tob-fix-review/
    └── SKILL.md
```

### 4.3 Naming Convention

Prefix all with `tob-` to:
- Identify source
- Avoid naming collisions
- Enable grouped management

## 5. Integration Points

### 5.1 Skill Invocation Triggers

| Trigger | Skills to Invoke |
|---------|------------------|
| "review PR", "security review" | `tob-differential-review` |
| "scan with semgrep", "quick security scan" | `tob-semgrep` |
| "deep analysis", "codeql" | `tob-codeql` |
| "find similar bugs", "variant analysis" | `tob-variant-analysis` |
| "dangerous patterns", "sharp edges" | `tob-sharp-edges` |
| "audit context", "deep context" | `tob-audit-context` |
| "review fix", "fix introduced bugs" | `tob-fix-review` |

### 5.2 CLAUDE.md Updates

Add to Auto-Invoke Triggers section:

```markdown
### Security Analysis Routing

| Context | Route To |
|---------|----------|
| PR review, commit review, security review | `tob-differential-review` |
| Quick security scan, semgrep, pattern scan | `tob-semgrep` |
| Deep analysis, codeql, interprocedural | `tob-codeql` |
| Similar bugs, variant analysis | `tob-variant-analysis` |
| Dangerous APIs, footguns, sharp edges | `tob-sharp-edges` |
| Audit prep, deep context building | `tob-audit-context` |
| Fix verification, regression check | `tob-fix-review` |
```

### 5.3 Slash Command Wrappers

Create user-friendly wrappers:

| Command | Maps To |
|---------|---------|
| `/security-review` | `tob-differential-review` |
| `/semgrep` | `tob-semgrep` |
| `/codeql` | `tob-codeql` |
| `/find-variants` | `tob-variant-analysis` |
| `/sharp-edges` | `tob-sharp-edges` |
| `/audit-context` | `tob-audit-context` |
| `/fix-review` | `tob-fix-review` |

## 6. Dependencies

### 6.1 External Tools Required

| Tool | Required By | Installation |
|------|-------------|--------------|
| Semgrep | `tob-semgrep` | `brew install semgrep` |
| CodeQL CLI | `tob-codeql` | `brew install codeql` |
| Git | All | Already installed |

### 6.2 No New Python Dependencies

All Trail of Bits skills use standard Claude tools (Bash, Read, Write, Grep, Glob).

## 7. Security Considerations

### 7.1 Allowed Tools Whitelist

Each skill declares explicit `allowed-tools` in frontmatter. Preserve these:

```yaml
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
  - Bash  # Required for git, semgrep, codeql
```

### 7.2 No Hooks Installed

Unlike the full plugin, we're NOT installing:
- `intercept-legacy-python.sh` hook
- Any pre-commit hooks

This preserves existing workflow.

## 8. Success Metrics

| Metric | Target |
|--------|--------|
| Skills installed | 7 of 7 Tier 1 |
| CLAUDE.md routing updated | Complete |
| Slash commands created | 7 wrappers |
| Semgrep installed | Verified |
| CodeQL installed | Verified |
| Test security review | 1 successful run |

## 9. Rollback Plan

If issues occur:
1. Remove skill folders from `~/.claude/skills/security/`
2. Revert CLAUDE.md routing changes
3. Delete slash command wrappers

All changes are isolated and reversible.

## 10. Timeline

| Phase | Tasks | Estimate |
|-------|-------|----------|
| Phase 1 | Clone repo, copy skills, prefix names | 10 min |
| Phase 2 | Install Semgrep + CodeQL | 5 min |
| Phase 3 | Update CLAUDE.md routing | 5 min |
| Phase 4 | Create slash command wrappers | 10 min |
| Phase 5 | Test with sample security review | 10 min |

**Total**: ~40 min

## 11. Future Enhancements

- Tier 2 skill evaluation (constant-time, property-based)
- Integration with existing `deliverable-reviewer` agent
- SARIF output parsing for structured findings
- RAG indexing of security findings

---

## Appendix A: Skill Frontmatter Templates

### tob-differential-review

```yaml
---
name: tob-differential-review
description: Security-focused code review for PRs and commits. Auto-invokes on "security review", "review PR for security".
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
  - Bash
---
```

### tob-semgrep

```yaml
---
name: tob-semgrep
description: Run Semgrep for fast security scanning. Auto-invokes on "semgrep", "quick security scan".
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
---
```

## Appendix B: Attribution

All skills derived from [trailofbits/skills](https://github.com/trailofbits/skills) under CC-BY-SA-4.0 license.

Required attribution in skill files:
```
# Source: Trail of Bits (https://github.com/trailofbits/skills)
# License: CC-BY-SA-4.0
```
