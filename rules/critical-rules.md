# Critical Rules (NEVER)

- NEVER skip discovery
- NEVER commit without explicit request
- NEVER hallucinate product capabilities
- NEVER create text walls without diagrams
- NEVER proceed silently with assumptions
- NEVER say "I don't have access to past conversations" - I DO (see Past Conversation Access)
- NEVER use Read tool on binary files (XLSX, DOCX, PPTX) - use Python
- NEVER trust DECISIONS.md alone for blocker status - cross-reference with conversation files
- NEVER retry MCP tools after failure - use CLI fallback immediately (see mcp-fast-fail rule)
- NEVER start RAG indexing without Ollama pre-flight check
- NEVER use direct git commit/push from ~ directory — use dotfiles scripts
- NEVER rewrite files >500 lines with Write tool — use targeted Edit with unique old_string

# Audit Trail ("Keep Receipts")

Every meaningful action should produce proof of: what was requested, what rules applied, what data was touched, what decision was made, and why it was allowed. When something breaks, read the receipt — don't debug vibes.

- Before destructive operations: state the action and rationale
- After bulk edits: log what changed and why (commit message, CTM context, or inline)
- For client-affecting decisions: record in DECISIONS.md with full rationale
- For data migrations: keep before/after counts and validation results

# Honesty & Failure Rules

- Failure is acceptable — NEVER force a "success" state by modifying tests, deleting checks, or stubbing real validations. If something is broken, report it broken.
- No silent failures — If a command or tool fails, report the failure immediately. NEVER pretend it worked or suppress the error.
- Flag cheating opportunities — If there's a way to technically satisfy a request but deceptively (e.g., hardcoding a test response, stubbing a real check), flag it as a potential misalignment and ask for clarification.
