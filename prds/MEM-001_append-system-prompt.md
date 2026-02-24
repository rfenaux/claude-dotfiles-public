# PRD: MEM-001 - Append System Prompt Enhancement

## Overview

### Problem Statement
The current system prompt injection mechanism in Claude Code CLI is all-or-nothing. When using `--system-prompt` to inject context, it completely replaces the existing CLAUDE.md instructions. This creates friction when users need temporary context additions for specific sessions without permanently modifying their CLAUDE.md files.

**Real-world scenario:**
- User has carefully crafted CLAUDE.md with global rules and preferences
- Needs to add temporary context for one session (e.g., "Focus on API security for this session")
- Current options: modify CLAUDE.md (persistence pollution) or replace entirely (lose all existing context)

### Proposed Solution
Introduce `--append-system-prompt` flag that adds supplementary instructions to the existing CLAUDE.md context rather than replacing it. This enables layered context injection:
- Base layer: CLAUDE.md (persistent, version-controlled)
- Session layer: --append-system-prompt (ephemeral, task-specific)

### Success Metrics
- **Adoption**: 30% of --system-prompt usage migrates to --append-system-prompt within 60 days
- **Quality**: Zero regression in context handling (existing --system-prompt behavior unchanged)
- **Performance**: No measurable increase in context window consumption vs. manual CLAUDE.md edits
- **User Satisfaction**: Positive feedback from beta testers on session-specific context workflows

---

## Requirements

### Functional Requirements

**FR-1: Append Flag Support**
- CLI must accept `--append-system-prompt <text|file>` flag
- Flag must support both inline text and file path (like --system-prompt)
- Must work with both global (`~/.claude/CLAUDE.md`) and project-local (`./CLAUDE.md`) files

**FR-2: Context Injection Order**
```
1. Base CLAUDE.md content (global + project)
2. Appended prompt content (from flag)
3. System behavior instructions (agent/skill protocols)
```

**FR-3: Conflict Detection**
- Warn if appended content contradicts base CLAUDE.md directives
- Provide --force flag to override warnings
- Log conflicts to debug output

**FR-4: Multi-append Support**
- Allow multiple `--append-system-prompt` flags in single invocation
- Apply in order specified on command line

**FR-5: Preview Mode**
- `--dry-run` flag shows final merged prompt without execution
- Output format shows clear delineation between base and appended sections

### Non-Functional Requirements

**NFR-1: Backward Compatibility**
- Existing `--system-prompt` behavior unchanged
- No breaking changes to current workflows

**NFR-2: Performance**
- Context merging adds <50ms to startup time
- Memory overhead <100KB for typical append operations

**NFR-3: Documentation**
- Update CLI help text
- Add examples to README.md
- Include in CONFIGURATION_GUIDE.md

**NFR-4: Token Efficiency**
- Deduplication of redundant instructions between base and append
- Optional compression of merged prompts (future)

### Out of Scope

- **Persistent append storage** (use CLAUDE.md for persistence)
- **GUI/TUI for prompt management** (CLI-only for MVP)
- **Conditional append logic** (no if/then rules in MVP)
- **Prompt version control** (leverage existing git workflows)
- **Cross-session append history** (ephemeral by design)

---

## Technical Design

### Architecture

**Component: Prompt Loader**
```
┌─────────────────────────────────────┐
│   CLI Argument Parser               │
│  - --system-prompt                  │
│  - --append-system-prompt (new)     │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   Prompt Merger                     │
│  1. Load base CLAUDE.md             │
│  2. Parse append sources            │
│  3. Detect conflicts (optional)     │
│  4. Merge with markers              │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   Context Injector                  │
│  - Inject into conversation system  │
│  - Preserve section boundaries      │
└─────────────────────────────────────┘
```

**Merge Strategy:**
```markdown
# Base CLAUDE.md Content
[existing instructions]

---
## SESSION CONTEXT (Appended)
[content from --append-system-prompt]

**Note:** Appended instructions take precedence over base instructions in case of conflict.
---

# System Behavior Instructions
[agent/skill protocols]
```

### Data Model

**Configuration Object:**
```typescript
interface PromptConfig {
  basePrompts: PromptSource[];      // CLAUDE.md files
  appendedPrompts: PromptSource[];  // --append-system-prompt sources
  systemPrompt?: string;            // --system-prompt (overrides all)
  mergeStrategy: 'append' | 'replace';
  conflictMode: 'warn' | 'force' | 'silent';
}

interface PromptSource {
  type: 'file' | 'inline';
  content: string;
  origin: string;  // file path or 'cli-arg'
  priority: number;
}
```

**Conflict Detection Schema:**
```typescript
interface ConflictRule {
  pattern: RegExp;          // e.g., /NEVER.*commit/i
  category: 'directive' | 'preference' | 'fact';
  severity: 'error' | 'warn' | 'info';
}
```

### API/Interface Changes

**CLI Interface:**
```bash
# Current (unchanged)
claude --system-prompt "Custom instructions"
claude --system-prompt /path/to/prompt.md

# New
claude --append-system-prompt "Temporary focus: API security"
claude --append-system-prompt /tmp/session-context.md

# Multiple appends
claude --append-system-prompt @security.md \
       --append-system-prompt @perf-testing.md

# Preview
claude --append-system-prompt "Test" --dry-run

# Force override conflicts
claude --append-system-prompt "COMMIT all changes" --force
```

**Programmatic API (if applicable):**
```typescript
// In claude-cli module
const session = new ClaudeSession({
  basePromptPaths: ['~/.claude/CLAUDE.md', './CLAUDE.md'],
  appendPrompts: [
    { type: 'inline', content: 'Focus on performance' },
    { type: 'file', path: '/tmp/context.md' }
  ],
  conflictMode: 'warn'
});
```

### Dependencies

**Required:**
- Existing prompt loading system (modify)
- CLI argument parser (extend)

**Optional:**
- Text similarity library for conflict detection (e.g., `string-similarity`)
- Markdown parser for structured merging (e.g., `marked`)

**Integration Points:**
- CLAUDE.md loader (global + project)
- Conversation context injector
- Debug/logging system (for conflict warnings)

---

## Implementation Plan

### Phase 1 (MVP)
**Goal:** Basic append functionality without conflict detection
**Duration:** 2-3 days

**Tasks:**
1. **CLI Parser Extension** (4h)
   - Add `--append-system-prompt` arg handling
   - Support file and inline text

2. **Prompt Merger** (6h)
   - Implement basic concatenation strategy
   - Add section markers (SESSION CONTEXT header)
   - Preserve base CLAUDE.md structure

3. **Testing** (4h)
   - Unit tests for merge logic
   - CLI integration tests
   - Manual testing with real CLAUDE.md files

4. **Documentation** (2h)
   - Update CLI help text
   - Add examples to README

**Deliverables:**
- Working `--append-system-prompt` flag
- Test suite covering basic scenarios
- Updated documentation

### Phase 2 (Enhancement)
**Goal:** Conflict detection and advanced features
**Duration:** 3-5 days

**Tasks:**
1. **Conflict Detection** (8h)
   - Define conflict patterns (NEVER/ALWAYS keywords)
   - Implement warning system
   - Add --force flag

2. **Multi-append Support** (4h)
   - Handle multiple --append-system-prompt flags
   - Priority ordering
   - Deduplication logic

3. **Preview Mode** (3h)
   - `--dry-run` implementation
   - Pretty-print merged prompt
   - Section highlighting

4. **Performance Optimization** (3h)
   - Cache merged prompts for session duration
   - Benchmark startup time impact

5. **Advanced Documentation** (2h)
   - Conflict detection guide
   - Best practices for session context
   - Integration with CTM workflows

**Deliverables:**
- Conflict detection with warnings
- Multi-append support
- Preview mode
- Performance benchmarks
- Comprehensive documentation

### Future Considerations

**Token Budget Awareness** (Future)
- Warn if appended content pushes near context limit
- Auto-trim low-priority sections
- Integration with existing context pruning system

**Prompt Templates** (Future)
- Pre-defined append templates (`@security`, `@performance`)
- Stored in `~/.claude/prompts/templates/`
- Quick invocation: `--append-template security`

**Session Persistence** (Future)
- Option to save appended context to `.claude/sessions/<session-id>.md`
- Replay previous session context: `--session-restore <id>`

**Smart Merge** (Future)
- Parse markdown structure of CLAUDE.md
- Insert appends at appropriate sections (e.g., under "## Current Focus")
- Maintain document coherence

---

## Verification Criteria

### Unit Tests

**Test Suite: Prompt Merger**
```typescript
describe('PromptMerger', () => {
  test('appends inline text to base prompt', () => {
    const base = 'Base instructions';
    const append = 'Session focus: testing';
    const result = merge(base, [append]);
    expect(result).toContain(base);
    expect(result).toContain(append);
    expect(result).toMatch(/SESSION CONTEXT/);
  });

  test('appends from file path', async () => {
    const base = 'Base instructions';
    const appendFile = '/tmp/test-append.md';
    // ... test implementation
  });

  test('handles multiple appends in order', () => {
    const appends = ['First', 'Second', 'Third'];
    const result = merge('Base', appends);
    const firstIdx = result.indexOf('First');
    const secondIdx = result.indexOf('Second');
    expect(firstIdx).toBeLessThan(secondIdx);
  });

  test('preserves base CLAUDE.md when no append', () => {
    const base = 'Original content';
    const result = merge(base, []);
    expect(result).toBe(base);
  });
});
```

**Test Suite: Conflict Detection**
```typescript
describe('ConflictDetector', () => {
  test('warns on contradicting NEVER directives', () => {
    const base = 'NEVER commit without approval';
    const append = 'Auto-commit all changes';
    const conflicts = detect(base, append);
    expect(conflicts).toHaveLength(1);
    expect(conflicts[0].severity).toBe('warn');
  });

  test('allows force override', () => {
    const config = { conflictMode: 'force' };
    const result = merge(base, append, config);
    expect(result).toContain(append);
  });
});
```

### Integration Tests

**Scenario 1: CLI End-to-End**
```bash
# Setup
echo "Base prompt" > /tmp/base.md
echo "Session context" > /tmp/append.md

# Execute
claude --system-prompt /tmp/base.md \
       --append-system-prompt /tmp/append.md \
       "Test query"

# Verify
# - Conversation includes both base and append
# - Section markers present
# - No errors/warnings
```

**Scenario 2: Conflict Warning**
```bash
# Setup CLAUDE.md with "NEVER commit without request"
# Execute with conflicting append
claude --append-system-prompt "Auto-commit all changes" \
       "Review code"

# Verify
# - Warning printed to stderr
# - Execution continues (warn mode)
# - Conflict logged to debug output
```

**Scenario 3: Multi-Append**
```bash
claude --append-system-prompt "Focus: security" \
       --append-system-prompt "Constraint: no external deps" \
       --append-system-prompt "Style: functional programming" \
       "Write auth module"

# Verify
# - All three appends in final prompt
# - Correct ordering maintained
```

### UAT Scenarios

**UAT-1: Temporary Security Focus**
- User has standard CLAUDE.md for general development
- Needs to review sensitive authentication code
- Uses `--append-system-prompt "CRITICAL: Audit for SQL injection and XSS vulnerabilities"`
- Claude provides security-focused review without user modifying CLAUDE.md

**UAT-2: Performance Testing Session**
- User starts performance optimization sprint
- Creates `perf-context.md` with benchmark targets and constraints
- Uses `--append-system-prompt perf-context.md` for multiple sessions
- After sprint, removes file (no CLAUDE.md pollution)

**UAT-3: Multi-Context Composition**
- User working on HubSpot + Salesforce integration
- Appends both `@hubspot-api-focus.md` and `@salesforce-mapping.md`
- Claude maintains awareness of both systems without permanent CLAUDE.md edits

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Context window bloat** | High | Medium | Implement token budget warnings; document best practices for concise appends |
| **Conflicting directives confuse model** | High | Medium | Conflict detection system; clear precedence rules in merged prompt |
| **Users misuse as permanent storage** | Medium | High | Documentation emphasizing ephemeral nature; suggest CLAUDE.md for persistence |
| **Performance degradation** | Medium | Low | Benchmark requirements (NFR-2); cache merged prompts |
| **Breaking changes to prompt structure** | High | Low | Comprehensive backward compatibility testing; feature flag for rollback |
| **Append sources become stale** | Low | Medium | Document file path usage; suggest absolute paths or project-relative |

**Mitigation Details:**

**Context Bloat Prevention:**
- Add `--verbose` flag to show token count of merged prompt
- Documentation: "Keep appends under 500 tokens for optimal performance"
- Future: Auto-trim redundant sections

**Conflict Resolution:**
- Clear precedence rule: "Appended instructions take precedence in case of conflict"
- Explicit marker in merged prompt
- User can review with `--dry-run`

**Misuse Prevention:**
- CLI warning if same append used >5 times: "Consider adding to CLAUDE.md"
- Documentation section: "When to use CLAUDE.md vs --append-system-prompt"

---

## Timeline Estimate

**Phase 1 (MVP):** 2-3 days
- Day 1: CLI parser + basic merger
- Day 2: Testing + documentation
- Day 3: Buffer for edge cases

**Phase 2 (Enhancement):** 3-5 days
- Week 1: Conflict detection + multi-append
- Week 2: Preview mode + optimization + docs

**Total:** 5-8 days for full implementation

**Milestones:**
- **Day 3:** MVP ready for internal testing
- **Day 5:** Beta release to select users
- **Day 8:** Full release with all enhancements

**Dependencies/Blockers:**
- Requires review of existing prompt loading architecture (Day 0)
- May need refactoring if current system doesn't support modular injection

**Follow-up Work:**
- Integration with CTM for auto-appending task context (MEM-003, future PRD)
- Prompt template library (separate PRD)

---

**Priority:** High impact, Low effort (quick win)
**Recommendation:** Implement immediately - solves a real pain point with minimal risk

---

*PRD Version: 1.0*
*Created: 2026-02-03*
*Author: Claude (Worker Agent)*
