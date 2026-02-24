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

## Recording

Use `decision-tracker` skill or add directly with A/T/P/S taxonomy.
