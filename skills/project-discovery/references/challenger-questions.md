# Challenger Questions Library

A comprehensive set of questions to validate requirements and challenge assumptions during project discovery.

## Existence Questions (Ask First)

These establish whether the project should exist at all.

### Project Justification
1. "Why are you leaving your current system? What's actually broken—not 'license expires,' but what pain are you solving?"
2. "What business outcome does this project need to produce? Give me a number that changes."
3. "What's the cost of doing nothing for 6 more months?"
4. "If we do this project perfectly, what metric improves? By how much?"

### Timeline Validation
5. "Is the deadline real or artificial? Has anyone tested if it's flexible?"
6. "Have you asked [current vendor] for a short-term extension?"
7. "What's the cost of a 60-day extension vs. the cost of rushing?"

### Success Definition
8. "When leadership reviews this project in 6 months, what number needs to have improved?"
9. "If we deliver on time but adoption is 30%, is that success?"
10. "Who decides when this project is 'done'? What are their criteria?"

---

## Scope Questions (Ask Second)

These determine what's actually essential vs. nice-to-have.

### Day 1 Requirements
11. "If the building was on fire, what 3 capabilities must work on Day 1?"
12. "What would block your team from working if it wasn't there?"
13. "Everything else—if it came 90 days later, would anyone's job be blocked?"

### Data Requirements
14. "How much of your historical data do you actually look at? When was the last time someone opened a record from 2+ years ago?"
15. "Of your [X] properties per object, how many have values on >50% of records?"
16. "What reports use this historical data? Who reads them? What decisions do they drive?"

### Simplification Opportunities
17. "Your current setup is complex. Do you want to replicate that complexity or escape it?"
18. "What have you built that you don't actually use?"
19. "What are you asking us to replicate that was a workaround in your old system?"
20. "If we gave you a clean slate, would you build it the same way?"

---

## Reality Questions (Ask Third)

These validate assumptions about the client's actual situation.

### Adoption Reality
21. "How many of your [X] users actually use the current system daily? Not licensed—active."
22. "What percentage of deals are in the CRM vs. in spreadsheets or someone's head?"
23. "If the CRM went down for a week, would work stop—or would nobody notice?"

### Client Capacity
24. "Who's the internal champion with 4-6 hours/week to make this succeed?"
25. "Who will answer questions and test configurations during implementation?"
26. "How will you communicate the change to your team? Do you have internal training resources?"

### Change Readiness
27. "On a scale of 1-10, how resistant is your team to changing their workflow?"
28. "Who are your power users? Who actively avoids the system?"
29. "What happened the last time you rolled out a new tool?"

---

## Module-Specific Challenger Questions

Use these when examining specific data modules or features.

### For Historical/Audit Modules
30. "What decision will someone make in [future year] that requires data from [past year]?"
31. "If the answer is 'audit' or 'just in case'—that's archive, not migration. Agree?"
32. "Who reads these audit reports? When was the last time they were generated?"

### For Custom Objects
33. "This is a custom [object]. What can you do with it as an object that you couldn't do with properties on [parent object]?"
34. "If we tracked this as [simpler alternative], what would you lose?"
35. "Does this need to be an entity with relationships, or is it just categorization?"

### For Integrations
36. "Of the [X] fields sent to [system], which are truly required vs. nice-to-have?"
37. "If we replaced the integration with a form that triggers [action], would that meet your needs?"
38. "What breaks if data is 5 minutes delayed vs. real-time?"

### For Reporting
39. "What are the 5 reports that absolutely must work on Day 1?"
40. "Who consumes these reports? What decisions do they make from them?"
41. "Can you show me those reports now? Are they actively used?"

### For Complex Pricing/Logic
42. "Walk me through the calculation for [formula field]. We need to rebuild this."
43. "Is this logic documented anywhere, or is it tribal knowledge?"
44. "What happens when the formula is wrong? How do you catch errors?"

### For Hierarchy/Structure
45. "How many levels deep is this hierarchy? Is it used in reporting roll-ups?"
46. "How often does this structure change?"
47. "Can we flatten this hierarchy, or is the parent-child relationship essential?"

---

## Budget Validation Questions

### Price Sensitivity
48. "If our final quote comes in at [X% over], is that a hard stop or a conversation?"
49. "What's the budget ceiling? What would make you walk away?"
50. "Is there flexibility to phase work to fit budget?"

### Value Alignment
51. "What's this problem costing you today? (Time, errors, missed opportunities)"
52. "If we solve this, what's the annual value? How did you calculate that?"
53. "Is this a cost-reduction project or a growth-enablement project?"

---

## Reframe Questions

Use these to shift the conversation from "what they asked for" to "what they need."

### Complexity Challenge
- "You built this because [old system] required it. [New system] handles this natively. Do you still need the workaround?"
- "This seems over-engineered for the problem. What am I missing?"
- "If you were starting from scratch today, would you build it this way?"

### Scope Challenge
- "We can either migrate your complexity or help you escape it. Which do you want?"
- "Every field we migrate is a field you maintain forever. Are you sure you need all of them?"
- "This is a migration project or an improvement project—which one are you buying?"

### Timeline Challenge
- "We can do this fast or do it right. A [X]-day extension would let us do it right. Worth exploring?"
- "What's the cost of fixing it later vs. doing it properly now?"
- "If we rush and something breaks at go-live, what's the impact?"

---

## The Meta-Question

Before asking anything, ask yourself:

> "If the client didn't have [current system], and we were implementing from scratch, would they ever ask for this?"

If no—it's legacy baggage, not a requirement.
