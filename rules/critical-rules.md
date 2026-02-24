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
- NEVER use direct git commit/push from ~ directory — use dotfiles-sync.sh / dotfiles-backup.sh
- NEVER rewrite files >500 lines with Write tool — use targeted Edit with unique old_string
