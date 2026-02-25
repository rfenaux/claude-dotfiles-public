# Decision Auto-Capture

Proactively detect and offer to record decisions and flag assumptions.

## Decision Detection

**Trigger phrases:**
- "we decided", "let's go with", "decision:", "the decision is"
- "we're going to use", "we'll use", "choosing", "we chose"
- "final answer", "that's the plan", "agreed"
- "instead of X, we'll do Y", "switching to"

**When detected:**
> "I notice we made a decision: **[decision summary]**. Want me to record this to DECISIONS.md?"

**Skip for:** Trivial decisions, already-recorded, exploratory discussions without commitment.

## Ambiguity Marking (OPEN / ASSUMED / MISSING)

Flag ambiguities explicitly rather than resolving them silently.

**Assumption triggers:** "I'll assume", "presumably", "I think this means", "probably", "likely means", interpreting vague requirements, filling gaps without confirmation.

**When making an assumption, mark inline:**
> `[ASSUMED: interpretation]` - verify with [source/person]

**When encountering unresolved questions:**
> `[OPEN: question]` - needs input from [whom]

**When info is referenced but absent:**
> `[MISSING: what's missing]` - referenced in [where]

**In decision records and summaries**, include an "Open Items" section with these markers. Offer to validate assumptions before proceeding on dependent work.

## Supersession Detection

**Trigger phrases:**
- "instead of [old], we're going with [new]"
- "we're changing the [decision] to"
- "that decision is outdated"
- "replacing [X] with [Y]", "overriding the previous decision"

**When supersession detected:**
1. Confirm what is being superseded (check DECISIONS.md for the active decision)
2. **Always ask for reason**: "What changed that makes [old decision] no longer valid?"
3. Do NOT record the supersession without a substantive reason
4. Format: Record reason in both the new decision (`Reason for supersession:`) and the superseded entry (`Why superseded:`)

**Reason quality check** — reject if:
- "Changed requirements" (too vague — ask what changed)
- "Better approach" (too vague — ask what evidence)
- Empty or "N/A"

**Acceptable reasons**: specific technical constraint discovered, vendor API change, stakeholder feedback with specifics, test/production failure revealing wrong assumption.

## Conditional Logic Preservation

Decisions lose nuance when recorded as simple statements. Preserve conditions explicitly.

**Template for conditions field:**
```
Conditions:
  VALID IF: [circumstances under which this decision holds]
  REVISIT IF: [trigger that should prompt re-evaluation]
  DEPENDS ON: [assumptions or external factors]
  VALID UNTIL: [expiry date or milestone, if applicable]
```

**Example:**
```
Decision: Use PostgreSQL SKIP LOCKED for dequeue
Conditions:
  VALID IF: message throughput < 10K/s
  REVISIT IF: scaling beyond single Postgres instance
  DEPENDS ON: connection pool max 25 being sufficient for MVP
  VALID UNTIL: post-launch load testing complete
```

**When to add conditions:** Any decision that involves trade-offs, scale thresholds, or assumptions about the environment. Skip for universal decisions ("use TypeScript for frontend").

## Recording

Use `decision-tracker` skill or add directly with A/T/P/S taxonomy.
