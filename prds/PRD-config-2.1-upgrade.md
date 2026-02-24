# PRD: Claude Code 2.1.x Configuration Upgrade

**Version:** 1.0
**Date:** 2026-02-04
**Status:** COMPLETED

---

## 1. Overview

Upgrade this Claude Code configuration to leverage new features introduced in Claude Code 2.1.x (v2.1.0 through v2.1.31).

### 1.1 Objectives

1. **Settings modernization** - Add new configuration options for better UX
2. **Permission cleanup** - Convert verbose patterns to cleaner wildcards
3. **Hook optimization** - Use `once: true` for single-run hooks
4. **Skill upgrades** - Add new frontmatter fields where beneficial
5. **StatusLine simplification** - Use new built-in percentage fields

### 1.2 Non-Goals

- Agent definition changes (separate initiative)
- Plugin upgrades (managed by plugin system)
- MCP server changes

---

## 2. Current State Analysis

### 2.1 settings.json

| Setting | Current | Gap |
|---------|---------|-----|
| `language` | Not set | Should be `"french"` for bilingual |
| `showTurnDuration` | Default (true) | Could hide "Cooked for X" noise |
| `spinnerVerbs` | Default | Could customize for signature style |
| `plansDirectory` | Not set | Should specify `~/.claude/plans` |
| `permissions.allow` | Verbose patterns | Needs wildcard cleanup |

### 2.2 Hooks

| Hook | Count | Issue |
|------|-------|-------|
| SessionStart | 3 | None use `once: true` |
| UserPromptSubmit | 5 | 1 could be `once: true` (enhance mode injection) |
| PreToolUse | 10 | All matcher-based, OK |
| PostToolUse | 6 | All matcher-based, OK |
| PreCompact | 3 | None need `once: true` |
| SessionEnd | 4 | None need `once: true` |

### 2.3 Skills Needing Upgrade

| Skill | Current | Upgrade Needed |
|-------|---------|----------------|
| `session-retro` | No `context: fork` | Add (spawns parallel workers) |
| `checkpoint` | No frontmatter | Add `context: fork` |
| `client-onboard` | No frontmatter | Add `context: fork`, `agent: general-purpose` |

### 2.4 Skills Already Using 2.1.x Features

- `brand-extract`: `context: fork`, `model: sonnet`
- `rag-batch-index`: `context: fork`, `agent: general-purpose`, `model: haiku`
- `action-extractor`: `context: fork`, `agent: general-purpose`

### 2.5 StatusLine

Current: Manual percentage calculation via jq arithmetic
New: Can use `context_window.used_percentage` directly

---

## 3. Changes Specification

### 3.1 settings.json Updates

#### 3.1.1 New Settings

```json
{
  "language": "french",
  "showTurnDuration": false,
  "spinnerVerbs": ["Cooking", "Architecting", "Configuring", "Brewing"],
  "plansDirectory": "~/.claude/plans"
}
```

#### 3.1.2 Permission Wildcards Cleanup

**After:**
```json
"allow": [
  "Bash(docker *)",
  "Bash(ffmpeg *)",
  "Bash(brew *)",
  "Bash(pip3 *)",
  "Bash(npm *)",
  "Bash(git *)",
  "Bash(mkdir *)",
  "Bash(curl *)",
  "Bash(whisper* *)",
  "Bash(mdfind *)",
  "Bash(find *)",
  "Bash(xargs *)",
  "Bash(stat *)",
  "Bash(*--help)",
  "Bash(*-h)",
  "Bash(*--version)"
]
```

#### 3.1.3 Hook Optimization

Add `once: true` to enhance mode injection hook.

### 3.2 Skill Frontmatter Upgrades

- `session-retro`: Add `context: fork`, `agent: general-purpose`, `model: haiku`
- `checkpoint`: Add `context: fork`, `agent: haiku`
- `client-onboard`: Add `context: fork`, `agent: general-purpose`, `model: sonnet`

### 3.3 StatusLine

Keep current implementation - test new fields first in future session.

---

## 4. Implementation Plan

### Phase 1: Settings Update
1. Backup current `settings.json`
2. Add new settings
3. Clean up permission wildcards
4. Add `once: true` to enhance mode hook

### Phase 2: Skill Upgrades
1. Update `session-retro` frontmatter
2. Update `checkpoint` frontmatter
3. Update `client-onboard` frontmatter

### Phase 3: Validation
1. Run `validate-setup.sh`
2. Test skill invocations

---

## 5. Files Modified

| File | Changes |
|------|---------|
| `~/.claude/settings.json` | New settings, permissions, hooks |
| `~/.claude/skills/session-retro/SKILL.md` | Frontmatter upgrade |
| `~/.claude/skills/checkpoint/SKILL.md` | Frontmatter upgrade |
| `~/.claude/skills/client-onboard/SKILL.md` | Frontmatter upgrade |
