# Organization Wiki Search (Cross-Project)

For any question touching organization process, methodology, or internal knowledge — search the organization wiki RAG **first**, regardless of current project.

> Skip this rule if `ORG_WIKI_PATH` is not set in your environment.

## Trigger Topics

Implementation methodology, BPM workshops, onboarding phases, badge pathways, SolA training, battlecards, quoting, KAM processes, TLO procedures, expenses, client service playbook, risk management, compliance, employee guides, HR policies, leave, dev SDLC, QA processes, cookie consent, email development, HubSpot partner updates.

## Search Path

```
rag_search(query, project_path="${ORG_WIKI_PATH}")
```

This index contains pages from your organization wiki (set ORG_WIKI_PATH to enable). Always available from any project directory.

## When to Search

| Situation | Action |
|-----------|--------|
| "How does our org do X?" | Search org-wiki RAG first |
| Implementation methodology question | Search org-wiki RAG first |
| Process/SOP question | Search org-wiki RAG first |
| HR/policy question | Search org-wiki RAG first |
| Starting a new client project | Search org-wiki for methodology |
| Quoting, scoping, risk assessment | Search org-wiki for procedures |

## Source Attribution

Always cite the wiki page filename when referencing organization wiki content.
