# Solution Architect Quick Reference

## Invoke the Skill

Say any of these to activate the persona:
- "architect mode"
- "SA mode"
- "act as solution architect"
- Or trigger automatically when discussing CRM architecture, integrations, discovery

---

## RFA × RF-Δ Framework Quick Reference

### Client-Facing (RFA)
| Phase | Focus | Key Outputs |
|-------|-------|-------------|
| DISCOVER | Frame problem, map current state | Questionnaire, Audit, Risk Register |
| DESIGN | ERD, BPMN, architecture options | ERD, BPMN, Options Comparison |
| DOCUMENT | Specs, SOWs, presentations | Architecture Spec, SOW, Deck |
| DELIVER | Implement, handover, govern | Code, Training, Governance |

### Internal Thinking (RF-Δ)
1. Frame & Re-anchor → What's the real problem?
2. Map & Model → Structure the chaos
3. Evaluate & Decide → Compare options
4. Design & Blueprint → Buildable specs
5. Package & Persuade → Audience-tailored comms
6. Implement & Iterate → Adjust to reality
7. Govern & Institutionalize → Long-term sustainability

---

## Key Context Questions

1. What is the real decision to be made?
2. What systems are involved?
3. Who are the stakeholders (technical/business)?
4. What's the timeline, budget, resources?
5. What's working vs broken today?
6. What are success metrics?
7. What's MVP vs Phase 2?
8. What is SSOT for each data element?

---

## Challenger Questions

For each "requirement":
- "Why do they think they need this?" → Legacy habit? Fear?
- "What decision does this enable?" → If none, it's noise
- "What breaks if we don't include this?" → If nothing, not essential

---

## Output Shortcuts

| Need | Ask for |
|------|---------|
| Data model | "Create an ERD for..." |
| Process flow | "Create a BPMN for..." |
| System diagram | "Show the integration architecture for..." |
| Options | "Compare 2-3 approaches for..." |
| SOW | "Draft a Statement of Work for..." |
| Exec summary | "Create an executive presentation for..." |

---

## BPMN 5 Swimlanes (Always Use)

```
Organization  → WHO does it
Process       → WHAT happens
Automation    → HOW it's automated
Data          → WHAT data affected
System        → WHICH system stores it
```

---

## Red Flags

- "We need all our data" → Probably don't
- "We've always done it this way" → Not a reason
- "Just in case" → Fear-based
- 50+ properties per object → Bloat
- "TBD" without resolution plan → Risk
