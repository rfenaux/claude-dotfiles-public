# PRD: MEM-002 - Claude Persistent Space (Autonomous Sessions)

## Overview

### Problem Statement
Claude currently operates only in synchronous, user-initiated sessions. Between human interactions, Claude cannot:
- Continue working on delegated tasks
- Monitor for trigger conditions (e.g., new files in inbox, scheduled maintenance)
- Perform background research or analysis
- Follow up on incomplete work from previous sessions

This creates a dependency on human presence for all work, even routine or time-delayed tasks that Claude could handle autonomously. Users must manually restart context and re-delegate work that could have been completed in the background.

**Real-world scenario:**
- User says "Research these 10 APIs and document them by tomorrow morning"
- Current: User must stay in session or return later to continue
- Desired: Claude works overnight, user finds completed documentation in the morning

### Proposed Solution
Introduce a "Persistent Space" where Claude can schedule and execute work autonomously between human sessions. This includes:
- **Deferred Task Queue**: Tasks Claude can work on when user is away
- **Scheduled Execution**: Cron-like triggers for recurring work
- **Autonomous Session Manager**: System to start Claude sessions without human input
- **Result Notification**: Alert user when autonomous work completes

This creates Claude's own "todo list" that runs independently of human sessions.

### Success Metrics
- **Autonomy Rate**: 20% of delegated tasks completed without human supervision within 90 days
- **Time Savings**: Users save average 30 minutes/day on routine tasks
- **Reliability**: 95% of scheduled tasks execute within ±5 minutes of scheduled time
- **Safety**: Zero unauthorized actions (all autonomous work pre-approved by user)
- **User Trust**: 80% of users enable autonomous mode after 30-day trial

---

## Requirements

### Functional Requirements

**FR-1: Persistent Task Queue**
- System maintains queue of deferred tasks at `~/.claude/persistent/queue.json`
- Each task includes: description, context, trigger conditions, authorization level
- Queue persists across system reboots and application restarts
- Tasks can be added from active sessions: `claude defer "Research XYZ APIs" --when "tonight at 11pm"`

**FR-2: Autonomous Session Triggers**
```
Trigger Types:
1. Time-based: Cron expressions (e.g., "0 2 * * *" for 2am daily)
2. Event-based: File system events (new file in inbox)
3. Condition-based: External state checks (API available, disk space >10GB)
4. Manual: User runs `claude-daemon execute-queue`
```

**FR-3: Authorization Model**
- **Level 1 (Read-only)**: Search, analyze, generate reports (no file writes)
- **Level 2 (Isolated writes)**: Write to designated directories only (e.g., `~/claude-output/`)
- **Level 3 (Full access)**: Any file operation (requires explicit user approval per task)
- Default: Level 1, user opts into higher levels per task

**FR-4: Session Management**
- Background daemon (`claude-daemon`) monitors queue and triggers
- Spawns autonomous sessions with limited context (no full conversation history)
- Session logs stored at `~/.claude/persistent/sessions/<task-id>/`
- Resource limits: max 30-minute runtime per task, max 100K tokens

**FR-5: Result Delivery**
- Completed work written to `~/claude-output/<task-id>/`
- Notification via: CLI status command, system notification, email (configurable)
- Summary report includes: task description, work performed, files created, issues encountered
- User can review and approve results before integration into main workspace

**FR-6: Safety Controls**
- Dry-run mode: Show what would be executed without actually running
- Kill switch: `claude-daemon stop` terminates all autonomous sessions
- Audit log: All autonomous actions logged with timestamps
- Sandbox mode: Execute in isolated environment (Docker container)

### Non-Functional Requirements

**NFR-1: Resource Management**
- Daemon uses <50MB RAM when idle
- Max 2 concurrent autonomous sessions
- Respect system load (pause if CPU >80% for 5 minutes)
- Token budget: 1M tokens/day for autonomous work (configurable)

**NFR-2: Reliability**
- Daemon auto-restarts on crash
- Queue persists to disk every 30 seconds
- Graceful shutdown: complete in-progress tasks before exit
- Failure recovery: retry failed tasks up to 3 times with exponential backoff

**NFR-3: Security**
- Autonomous sessions run with restricted API key (if applicable)
- No access to credentials in `~/.ssh`, `~/.aws`, etc. (configurable whitelist)
- File operations logged for audit
- Network access restricted (optional firewall rules)

**NFR-4: User Experience**
- `claude-daemon status` shows queue and running tasks
- `claude-daemon logs <task-id>` views session output
- `claude-daemon approve <task-id>` integrates completed work
- Visual dashboard at `http://localhost:8420/persistent` (extends existing dashboard)

### Out of Scope

- **Multi-user support** (single-user system for MVP)
- **Distributed execution** (runs on local machine only)
- **Cloud synchronization** (no automatic sync to remote systems)
- **Advanced scheduling** (no dependency graphs between tasks)
- **Interactive tasks** (no mid-task user input during autonomous execution)

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────┐
│   User Session (Interactive)        │
│  - claude defer "task" --when "..."│
│  - claude-daemon status             │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   Claude Daemon (Background)        │
│  - Queue Monitor                    │
│  - Trigger Evaluator                │
│  - Session Spawner                  │
└────────────┬────────────────────────┘
             │
             ├──────────────────────────────┐
             ▼                              ▼
┌──────────────────────┐      ┌──────────────────────┐
│ Autonomous Session 1 │      │ Autonomous Session 2 │
│ - Limited context    │      │ - Limited context    │
│ - Task-specific auth │      │ - Task-specific auth │
│ - Output to sandbox  │      │ - Output to sandbox  │
└──────────┬───────────┘      └──────────┬───────────┘
           │                              │
           ▼                              ▼
┌─────────────────────────────────────────────────────┐
│   Result Storage                                    │
│  ~/claude-output/<task-id>/                        │
│  - OUTPUT.md (summary)                             │
│  - artifacts/ (generated files)                    │
│  - session.log (full execution log)                │
└─────────────────────────────────────────────────────┘
```

**Component Interaction:**
1. User defers task via `claude defer` command
2. Task added to queue with trigger condition
3. Daemon monitors queue, evaluates triggers
4. When triggered, daemon spawns autonomous session
5. Session executes task with limited context/permissions
6. Results written to isolated output directory
7. User notified, reviews, and approves/rejects results

### Data Model

**Task Queue Schema:**
```typescript
interface PersistentTask {
  id: string;                    // UUID
  description: string;           // Human-readable task description
  prompt: string;                // Full prompt for Claude session
  context: TaskContext;          // CTM state, relevant files
  trigger: Trigger;              // When to execute
  authorization: AuthLevel;      // Permission level
  status: 'pending' | 'running' | 'completed' | 'failed';
  createdAt: Date;
  scheduledFor?: Date;
  executedAt?: Date;
  completedAt?: Date;
  retryCount: number;
  output?: TaskOutput;
}

interface Trigger {
  type: 'time' | 'event' | 'condition' | 'manual';
  schedule?: string;             // Cron expression for time-based
  eventPattern?: string;         // File glob for event-based
  conditionScript?: string;      // Shell script for condition-based
}

interface TaskContext {
  ctmState?: string;             // Serialized CTM context
  workingDirectory: string;
  relevantFiles: string[];       // Paths to files Claude should know about
  environmentVars: Record<string, string>;
}

interface AuthLevel {
  level: 1 | 2 | 3;
  allowedPaths?: string[];       // For level 2
  deniedPaths: string[];         // Explicit exclusions
  allowNetworkAccess: boolean;
}

interface TaskOutput {
  summary: string;               // High-level summary of work done
  artifacts: Artifact[];         // Files created/modified
  logs: string;                  // Session execution log
  errors?: string[];             // Any errors encountered
  tokenUsage: number;
}

interface Artifact {
  path: string;                  // Relative to output directory
  type: 'file' | 'directory';
  description: string;
}
```

**Daemon State:**
```typescript
interface DaemonState {
  running: boolean;
  activeSessions: ActiveSession[];
  queue: PersistentTask[];
  tokenUsageToday: number;
  lastHealthCheck: Date;
  config: DaemonConfig;
}

interface ActiveSession {
  taskId: string;
  pid: number;
  startedAt: Date;
  tokenUsage: number;
  status: 'initializing' | 'running' | 'completing' | 'error';
}

interface DaemonConfig {
  maxConcurrentSessions: number;
  maxTokensPerDay: number;
  maxRuntimePerTask: number;      // seconds
  checkInterval: number;           // seconds between queue checks
  notificationMethod: 'cli' | 'system' | 'email';
  sandboxMode: boolean;
}
```

### API/Interface Changes

**CLI Commands:**
```bash
# Defer a task
claude defer "Research top 5 React state management libraries" \
       --when "tonight at 11pm" \
       --auth-level 2 \
       --output ~/projects/research/

# Daemon management
claude-daemon start                    # Start background daemon
claude-daemon stop                     # Stop daemon
claude-daemon restart                  # Restart daemon
claude-daemon status                   # Show queue and active sessions

# Task management
claude-daemon list                     # List all queued tasks
claude-daemon cancel <task-id>         # Remove task from queue
claude-daemon logs <task-id>           # View session logs
claude-daemon retry <task-id>          # Manually retry failed task

# Result handling
claude-daemon review <task-id>         # Show task output summary
claude-daemon approve <task-id>        # Move results to main workspace
claude-daemon reject <task-id>         # Discard results

# Configuration
claude-daemon config set max-concurrent 3
claude-daemon config set token-budget 2000000
```

**Programmatic API:**
```typescript
// In claude-cli module
import { PersistentSpace } from 'claude-code/persistent';

const space = new PersistentSpace();

// Defer task
await space.defer({
  description: 'Generate API documentation',
  prompt: 'Create OpenAPI spec for REST API at localhost:3000',
  trigger: { type: 'time', schedule: '0 2 * * *' },  // 2am daily
  authorization: { level: 2, allowedPaths: ['~/docs/'] }
});

// Monitor queue
const tasks = await space.listTasks({ status: 'pending' });

// Get results
const output = await space.getTaskOutput('task-id-123');
```

### Dependencies

**Required:**
- Node.js daemon framework (e.g., `pm2`, `systemd` integration, or custom)
- Task scheduler (e.g., `node-cron`)
- File system watcher (e.g., `chokidar`)
- IPC mechanism for daemon-CLI communication (Unix sockets or HTTP)

**Optional:**
- Docker for sandbox mode
- SMTP library for email notifications (e.g., `nodemailer`)
- System notification library (e.g., `node-notifier`)

**Integration Points:**
- Existing Claude session initialization code
- CTM system (serialize/deserialize task context)
- Authorization/permission system (extend existing if present)
- Dashboard web interface (extend existing)

---

## Implementation Plan

### Phase 1 (MVP)
**Goal:** Basic deferred task execution with time-based triggers
**Duration:** 2-3 weeks

**Tasks:**
1. **Daemon Infrastructure** (1 week)
   - Background process manager
   - Queue persistence (JSON file)
   - Basic trigger evaluator (time-based only)
   - Session spawning logic

2. **CLI Integration** (3 days)
   - `claude defer` command
   - `claude-daemon` subcommands (start, stop, status, list)
   - Configuration management

3. **Autonomous Session** (4 days)
   - Limited context initialization (no full history)
   - Output isolation (write to sandbox directory)
   - Basic authorization (read-only vs. write-allowed paths)

4. **Result Handling** (2 days)
   - Output directory structure
   - Summary report generation
   - Basic approval workflow (`approve`/`reject`)

5. **Testing** (3 days)
   - Unit tests for queue operations
   - Integration tests for end-to-end flow
   - Manual testing with real tasks

6. **Documentation** (2 days)
   - Architecture overview
   - User guide for deferring tasks
   - Security best practices

**Deliverables:**
- Working daemon that executes time-based deferred tasks
- CLI commands for task management
- Basic authorization model (levels 1-2)
- Documentation

**Success Criteria:**
- User can defer task with `--when "in 5 minutes"`
- Daemon executes task automatically
- Results appear in `~/claude-output/`
- No unauthorized file access

### Phase 2 (Enhancement)
**Goal:** Event-based triggers, advanced features, dashboard
**Duration:** 2-3 weeks

**Tasks:**
1. **Event-Based Triggers** (1 week)
   - File system watcher integration
   - Inbox monitoring pattern
   - Custom event types

2. **Advanced Authorization** (3 days)
   - Level 3 (full access) with explicit approval
   - Per-task permission review UI
   - Audit logging

3. **Notification System** (3 days)
   - System notifications (macOS/Linux)
   - Email notifications
   - Webhook support

4. **Dashboard Integration** (1 week)
   - Queue visualization at `/persistent`
   - Live session monitoring
   - Task approval workflow

5. **Resource Management** (3 days)
   - Token budget enforcement
   - System load monitoring
   - Concurrent session limits

6. **Reliability** (4 days)
   - Retry logic with exponential backoff
   - Graceful shutdown
   - Auto-restart on crash

7. **Testing & Hardening** (1 week)
   - Stress testing (100+ queued tasks)
   - Failure scenario testing
   - Security audit

**Deliverables:**
- Event-based triggers (file inbox monitoring)
- Full authorization model (levels 1-3)
- Web dashboard for persistent space
- Notification system
- Production-ready reliability

### Future Considerations

**Sandbox Execution** (Phase 3)
- Run autonomous sessions in Docker containers
- Full filesystem isolation
- Network restrictions

**Distributed Execution** (Future)
- Run tasks on remote machines
- Cloud integration (AWS Lambda, GitHub Actions)

**Task Dependencies** (Future)
- DAG-based task scheduling
- "Execute B only if A succeeds"

**Interactive Checkpoints** (Future)
- Mid-task user input
- "Pause and ask user for clarification"

**Learning & Optimization** (Future)
- Analyze which deferred tasks succeed/fail
- Suggest optimal scheduling times
- Auto-adjust resource limits

---

## Verification Criteria

### Unit Tests

**Test Suite: Task Queue**
```typescript
describe('TaskQueue', () => {
  test('adds task to queue', async () => {
    const queue = new TaskQueue();
    const task = createMockTask();
    await queue.add(task);
    expect(queue.list()).toContainEqual(task);
  });

  test('persists queue to disk', async () => {
    const queue = new TaskQueue('/tmp/test-queue.json');
    await queue.add(createMockTask());
    const reloaded = new TaskQueue('/tmp/test-queue.json');
    await reloaded.load();
    expect(reloaded.list()).toHaveLength(1);
  });

  test('removes completed tasks', async () => {
    const queue = new TaskQueue();
    const task = await queue.add(createMockTask());
    await queue.markCompleted(task.id);
    expect(queue.list()).toHaveLength(0);
  });
});
```

**Test Suite: Trigger Evaluation**
```typescript
describe('TriggerEvaluator', () => {
  test('evaluates time-based trigger', () => {
    const trigger = { type: 'time', schedule: '* * * * *' }; // every minute
    const evaluator = new TriggerEvaluator();
    expect(evaluator.shouldExecute(trigger)).toBe(true);
  });

  test('evaluates event-based trigger', async () => {
    const trigger = { type: 'event', eventPattern: '~/inbox/*.md' };
    const evaluator = new TriggerEvaluator();
    fs.writeFileSync('~/inbox/test.md', 'content');
    await sleep(100);  // Wait for file system event
    expect(evaluator.shouldExecute(trigger)).toBe(true);
  });
});
```

**Test Suite: Authorization**
```typescript
describe('Authorization', () => {
  test('level 1 blocks file writes', () => {
    const auth = new Authorization({ level: 1 });
    expect(() => auth.checkWrite('/any/path')).toThrow();
  });

  test('level 2 allows writes to allowed paths', () => {
    const auth = new Authorization({
      level: 2,
      allowedPaths: ['~/claude-output/']
    });
    expect(() => auth.checkWrite('~/claude-output/file.txt')).not.toThrow();
    expect(() => auth.checkWrite('~/other/file.txt')).toThrow();
  });

  test('level 3 allows all writes', () => {
    const auth = new Authorization({ level: 3 });
    expect(() => auth.checkWrite('/any/path')).not.toThrow();
  });
});
```

### Integration Tests

**Scenario 1: End-to-End Deferred Task**
```bash
# Start daemon
claude-daemon start

# Defer task
claude defer "Create README.md with project overview" \
       --when "in 30 seconds" \
       --auth-level 2 \
       --output ~/test-output/

# Wait for execution
sleep 35

# Verify
claude-daemon status  # Should show completed task
ls ~/test-output/     # Should contain README.md
claude-daemon review $(claude-daemon list --last)  # Show summary
```

**Scenario 2: Event-Based Trigger**
```bash
# Configure inbox monitoring
claude defer "Process new files in inbox" \
       --when "file:~/inbox/*.txt" \
       --auth-level 2

# Trigger event
echo "Test content" > ~/inbox/test.txt

# Wait for processing
sleep 5

# Verify
claude-daemon logs $(claude-daemon list --last)
```

**Scenario 3: Authorization Enforcement**
```bash
# Attempt unauthorized write
claude defer "Write to system directory" \
       --when "now" \
       --auth-level 1 \
       --output /etc/

# Verify failure
claude-daemon logs $(claude-daemon list --last) | grep "Permission denied"
```

### UAT Scenarios

**UAT-1: Overnight Research**
- User: "Research top 10 GraphQL servers and document pros/cons"
- Action: `claude defer "Research..." --when "tonight at 11pm" --auth-level 2`
- Morning: User finds `~/claude-output/<task-id>/research.md` with detailed analysis
- User reviews, approves, moves to project docs

**UAT-2: Inbox Processing**
- User drops meeting notes into `~/inbox/`
- Daemon auto-detects new files
- Autonomous session extracts action items, creates tasks in CTM
- User arrives to find processed notes and task list ready

**UAT-3: Scheduled Maintenance**
- User schedules daily 2am task: "Update dependencies, run tests, generate report"
- Task runs nightly with full write access (auth level 3, pre-approved)
- User gets morning notification: "8/10 dependencies updated, all tests pass"
- User reviews changes, approves pull request

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Unauthorized actions** | Critical | Medium | Multi-level authorization; audit logging; sandbox mode; explicit user approval |
| **Resource exhaustion** | High | Medium | Token budgets; runtime limits; concurrent session caps; system load monitoring |
| **Data loss from failed tasks** | High | Low | Persistent queue; retry logic; comprehensive error logging |
| **User confusion about autonomous work** | Medium | High | Clear notifications; approval workflow; detailed session logs; dashboard visibility |
| **Security vulnerabilities** | Critical | Low | Restricted API keys; path whitelisting; network restrictions; security audit |
| **Daemon crashes** | Medium | Medium | Auto-restart; graceful shutdown; in-progress task recovery |
| **Token budget abuse** | Medium | Low | Daily limits; per-task limits; cost monitoring alerts |
| **Conflicting with interactive sessions** | Medium | Medium | Resource coordination; queue priority system; pause mechanism |

**Mitigation Details:**

**Security Model:**
- **Principle of Least Privilege**: Default auth level 1 (read-only)
- **Explicit Opt-In**: User must approve each level 3 task
- **Audit Trail**: All file operations logged with timestamps
- **Isolation**: Sandbox mode for untrusted tasks

**Resource Management:**
- **Token Budget**: Hard limit 1M tokens/day (configurable)
- **Runtime Limits**: 30-minute max per task (prevents runaway processes)
- **System Health**: Pause if CPU >80% or memory >90%

**User Trust Building:**
- **Transparency**: Dashboard shows exactly what daemon is doing
- **Control**: Kill switch stops all autonomous work immediately
- **Dry Run**: Preview what would be executed before enabling
- **Gradual Adoption**: Start with read-only tasks, build trust, expand permissions

---

## Timeline Estimate

**Phase 1 (MVP):** 2-3 weeks
- Week 1: Daemon infrastructure + basic queue
- Week 2: Session spawning + authorization
- Week 3: Testing + documentation

**Phase 2 (Enhancement):** 2-3 weeks
- Week 1: Event triggers + notifications
- Week 2: Dashboard + advanced features
- Week 3: Reliability + security hardening

**Total:** 4-6 weeks for production-ready system

**Milestones:**
- **Week 2:** MVP functional (time-based deferred tasks work)
- **Week 3:** Internal beta testing
- **Week 4:** Event-based triggers working
- **Week 5:** Dashboard live
- **Week 6:** Public beta release

**Dependencies/Blockers:**
- **Security Review Required**: External security audit before public release
- **UX Validation**: User testing to validate approval workflow
- **Infrastructure**: Decision on daemon framework (pm2 vs. systemd vs. custom)

**Follow-up Work:**
- **MEM-003**: CTM integration for auto-spawning deferred tasks
- **MEM-004**: Distributed execution for cloud environments
- **MEM-005**: Interactive checkpoint system for complex tasks

---

## Open Questions

1. **Daemon Lifecycle**: Should daemon auto-start on system boot? (Security implications)
2. **Token Costs**: Who pays for autonomous token usage? (Org vs. personal API keys)
3. **Failure Notifications**: How aggressive should error notifications be? (Avoid alert fatigue)
4. **Multi-project Support**: Should queue be global or per-project?
5. **Cloud Integration**: AWS/GCP execution in scope for Phase 2? (Infrastructure complexity)

**Recommended Approach:**
- Start with opt-in auto-start (user enables via `claude-daemon install`)
- Personal API keys for MVP, org billing in Phase 2
- Email digests for failures (not real-time alerts)
- Global queue with project context in task metadata
- Cloud execution deferred to Phase 3 (focus on local first)

---

**Priority:** Medium impact, High effort (future exploration)
**Recommendation:** Plan for Q2 implementation after quick wins (MEM-001, TOOL-003) are complete

---

*PRD Version: 1.0*
*Created: 2026-02-03*
*Author: Claude (Worker Agent)*
